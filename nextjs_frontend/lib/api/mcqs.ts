/**
 * MCQ API
 * Handles MCQ generation, saving, and exam PDF generation
 */

import { get, post, del } from './client';

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
}

export interface MCQSet {
  doc_id: string;
  analysis: any;
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
 * Generate MCQs for a specific chapter
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

