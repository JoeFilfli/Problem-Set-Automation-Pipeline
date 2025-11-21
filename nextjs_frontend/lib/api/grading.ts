/**
 * Grading API
 * Handles submission grading and evaluation
 */

import { post } from './client';
import type {
  GradeSubmissionsRequest,
  GradeSubmissionsResponse,
  Problem,
} from '../types';

/**
 * Grade multiple student submissions for a problem
 */
export async function gradeSubmissions(
  problem: Problem,
  correctSolution: string,
  studentSubmissions: Array<{ name: string; solution: string }>
): Promise<GradeSubmissionsResponse> {
  return post<GradeSubmissionsResponse>('/api/py/grade-submissions', {
    problem,
    correct_solution: correctSolution,
    student_submissions: studentSubmissions,
  });
}

/**
 * Calculate grade letter from percentage
 */
export function getGradeLetter(percentage: number): string {
  if (percentage >= 90) return 'A';
  if (percentage >= 85) return 'A-';
  if (percentage >= 80) return 'B+';
  if (percentage >= 75) return 'B';
  if (percentage >= 70) return 'B-';
  if (percentage >= 65) return 'C+';
  if (percentage >= 60) return 'C';
  if (percentage >= 55) return 'C-';
  if (percentage >= 50) return 'D';
  return 'F';
}

/**
 * Get color class for grade
 */
export function getGradeColor(percentage: number): string {
  if (percentage >= 80) return 'text-green-600';
  if (percentage >= 70) return 'text-yellow-600';
  if (percentage >= 60) return 'text-orange-600';
  return 'text-red-600';
}

