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
  const response = await fetch('/api/py/generate-exam-pdf', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      mcq_ids: mcqIds,
      exam_title: examTitle,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate exam PDF');
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

