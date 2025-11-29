/**
 * MCQ API
 * Handles MCQ generation, saving, and exam PDF generation
 */

import { get, post, del } from './client';
import { buildApiUrl } from './client';

export interface MCQ {
  id: number;
  difficulty: string;
  topic: string;
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correct_answer: string;
  explanation: string;
  question_type?: 'analytical' | 'direct'; // Added by PromptBuilderAgent
}

export interface MCQSet {
  doc_id: string;
  analysis: any;
  prompt_info?: {
    domain: string;
    content_type: string;
    complexity: string;
    key_characteristics: string[];
    recommended_focus_areas: string[];
  };
  num_mcqs: number;
  mcqs: MCQ[];
}

export interface SavedMCQ {
  id: string;
  mcq: MCQ;
  chapter: string;
  saved_at: string;
}

/**
 * Stream event types for MCQ generation
 */
export type MCQStreamEvent =
  | { type: 'status'; message: string; step?: number; substep?: string; complete?: boolean }
  | { type: 'prompt_info'; data: MCQSet['prompt_info'] }
  | { type: 'analysis'; data: any }
  | { type: 'mcq'; data: MCQ }
  | { type: 'done'; doc_id: string }
  | { type: 'error'; message: string; traceback?: string };

/**
 * Generate MCQs for a specific chapter (non-streaming)
 */
export async function generateMCQs(
  docId: string,
  numMCQs: number = 5
): Promise<MCQSet> {
  const response = await post<{ success: boolean; mcq_set: MCQSet }>(
    '/api/py/generate-mcqs',
    {
      doc_id: docId,
      num_mcqs: numMCQs,
    }
  );
  return response.mcq_set;
}

/**
 * Stream MCQ generation - progressive updates as questions are generated
 */
export async function streamMCQGeneration(
  docId: string,
  numMCQs: number,
  onEvent: (event: MCQStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const url = buildApiUrl('/api/py/generate-mcqs/stream');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doc_id: docId,
      num_mcqs: numMCQs,
    }),
    signal,
  });

  if (!response.ok || !response.body) {
    let detail = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || data.error || detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line) as MCQStreamEvent;
        onEvent(event);
      } catch (err) {
        console.error('Failed to parse stream event', err, line);
      }
    }
  }
}

/**
 * Save a selected MCQ
 */
export async function saveMCQ(
  mcq: MCQ,
  chapter: string
): Promise<{ success: boolean; mcq_id: string; mcq: SavedMCQ }> {
  return await post('/api/py/save-mcq', {
    mcq,
    chapter,
  });
}

/**
 * Get all saved MCQs
 */
export async function getSavedMCQs(): Promise<{
  success: boolean;
  total: number;
  mcqs: SavedMCQ[];
}> {
  return await get('/api/py/saved-mcqs');
}

/**
 * Delete a saved MCQ
 */
export async function deleteSavedMCQ(mcqId: string): Promise<{
  success: boolean;
  message: string;
}> {
  return await del(`/api/py/saved-mcqs/${mcqId}`);
}

/**
 * Generate exam PDF from saved MCQs
 */
export async function generateExamPDF(
  mcqIds: string[],
  examTitle?: string
): Promise<Blob> {
  const url = buildApiUrl('/api/py/generate-exam-pdf');
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      mcq_ids: mcqIds,
      exam_title: examTitle,
    }),
  });

  // Check content type first
  const contentType = response.headers.get('content-type') || '';
  
  if (!response.ok) {
    // Handle error response
    let errorMessage = `Failed to generate exam PDF (HTTP ${response.status})`;
    
    try {
      // Clone response to read it without consuming the original
      const responseClone = response.clone();
      const text = await responseClone.text();
      
      console.error('[generateExamPDF] Error response:', {
        status: response.status,
        contentType,
        textPreview: text.substring(0, 200)
      });
      
      // Try to parse as JSON
      if (contentType.includes('application/json')) {
        try {
          const error = JSON.parse(text);
          errorMessage = error.detail || error.message || errorMessage;
        } catch (parseError) {
          // If JSON parsing fails, try to extract from text
          const jsonMatch = text.match(/"detail"\s*:\s*"([^"]+)"/i) || 
                           text.match(/"message"\s*:\s*"([^"]+)"/i) ||
                           text.match(/"error"\s*:\s*"([^"]+)"/i);
          if (jsonMatch && jsonMatch[1]) {
            errorMessage = jsonMatch[1].replace(/\\"/g, '"').replace(/\\n/g, ' ');
          } else {
            // If it starts with <, it's probably HTML
            if (text.trim().startsWith('<')) {
              errorMessage = `Server returned HTML instead of JSON. This usually means the backend encountered an error. Status: ${response.status}`;
            }
          }
        }
      } else if (text.includes('<!DOCTYPE') || text.includes('<html') || text.trim().startsWith('<')) {
        // It's HTML - try to extract error message
        const htmlMatch = text.match(/<title>(.*?)<\/title>/i) || 
                         text.match(/<h1[^>]*>(.*?)<\/h1>/i) ||
                         text.match(/<body[^>]*>(.*?)<\/body>/is);
        if (htmlMatch && htmlMatch[1]) {
          // Clean up HTML tags
          errorMessage = htmlMatch[1].replace(/<[^>]+>/g, '').trim();
          if (errorMessage.length > 200) {
            errorMessage = errorMessage.substring(0, 200) + '...';
          }
        } else {
          errorMessage = `Server returned HTML error page (HTTP ${response.status}). Check backend logs for details.`;
        }
      } else if (text.length > 0 && text.length < 1000) {
        // It's plain text and not too long
        errorMessage = text.trim();
      }
    } catch (readError) {
      // If we can't read the response, use the default error message
      console.error('[generateExamPDF] Error reading error response:', readError);
    }
    
    throw new Error(errorMessage);
  }

  // Response is OK - verify it's actually a PDF
  if (!contentType.includes('application/pdf') && !contentType.includes('application/octet-stream')) {
    // If it's not a PDF, it might be an error response that got through
    try {
      const text = await response.text();
      let errorMessage = `Expected PDF but received ${contentType}`;
      
      // Try to parse as JSON error
      try {
        const error = JSON.parse(text);
        errorMessage = error.detail || error.message || errorMessage;
      } catch {
        // If not JSON, check if it's HTML
        if (text.includes('<!DOCTYPE') || text.includes('<html')) {
          const match = text.match(/<title>(.*?)<\/title>/i) || text.match(/<h1[^>]*>(.*?)<\/h1>/i);
          if (match && match[1]) {
            errorMessage = match[1].trim();
          }
        } else if (text.length < 500) {
          errorMessage = text.trim();
        }
      }
      
      throw new Error(errorMessage);
    } catch (readError) {
      throw new Error(`Expected PDF but received ${contentType}. Unable to read error details.`);
    }
  }

  return await response.blob();
}

/**
 * Download exam PDF
 */
export function downloadExamPDF(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

