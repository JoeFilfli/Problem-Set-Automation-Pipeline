/**
 * Problem Sets API
 * Handles problem set generation and management
 */

import { get, post } from './client';
import type {
  GenerateProblemSetRequest,
  GenerateProblemSetResponse,
  ProblemSet,
} from '../types';

/**
 * Generate a problem set for a specific chapter
 */
export async function generateProblemSet(
  request: GenerateProblemSetRequest
): Promise<ProblemSet> {
  const response = await post<GenerateProblemSetResponse>(
    '/api/py/generate-problem-set',
    request
  );
  return response.problem_set;
}

/**
 * Batch generate problem sets for multiple chapters
 */
export async function batchGenerateProblemSets(
  docIds: string[],
  numProblems: number = 5,
  checkQuality: boolean = true
): Promise<Array<{ doc_id: string; success: boolean; problem_set?: ProblemSet; error?: string }>> {
  const response = await post<{
    success: boolean;
    results: Array<{
      doc_id: string;
      success: boolean;
      problem_set?: ProblemSet;
      error?: string;
    }>;
  }>('/api/py/batch-generate-problem-sets', {
    doc_ids: docIds,
    num_problems: numProblems,
    check_quality: checkQuality,
  });
  
  return response.results || [];
}

/**
 * Export problem set in different formats
 */
export async function exportProblemSet(
  problemSet: ProblemSet,
  format: 'markdown' | 'json' | 'problems_only' = 'markdown'
): Promise<{ content: string; filename: string }> {
  const response = await post<{
    success: boolean;
    format: string;
    content: string;
    filename: string;
  }>('/api/py/export-problem-set', {
    problem_set: problemSet,
    format,
  });
  
  return {
    content: response.content,
    filename: response.filename,
  };
}

/**
 * Download exported problem set
 */
export function downloadProblemSet(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

