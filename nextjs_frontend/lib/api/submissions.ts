/**
 * API Client for Problem Sets and Submissions
 * 
 * This module interacts with the FastAPI backend endpoints for storing
 * and retrieving problem sets and student submissions.
 */

import { get, post, put, del } from './client';

const API_BASE = '/api/py';

// ============================================================================
// PROBLEM SET API
// ============================================================================

/**
 * Get all problem sets from the backend
 */
export async function getAllProblemSets(): Promise<any[]> {
  try {
    const response = await get<{ success: boolean; total: number; problem_sets: any[] }>(
      `${API_BASE}/problem-sets`
    );
    return response.problem_sets || [];
  } catch (error) {
    console.error('Error fetching problem sets:', error);
    return [];
  }
}

/**
 * Get a specific problem set by ID
 */
export async function getProblemSet(problemSetId: string): Promise<any | null> {
  try {
    const response = await get<{ success: boolean; problem_set: any }>(
      `${API_BASE}/problem-sets/${problemSetId}`
    );
    return response.problem_set;
  } catch (error) {
    console.error('Error fetching problem set:', error);
    return null;
  }
}

/**
 * Delete a problem set
 */
export async function deleteProblemSet(problemSetId: string): Promise<void> {
  await del(`${API_BASE}/problem-sets/${problemSetId}`);
}

// ============================================================================
// SUBMISSION API
// ============================================================================

/**
 * Store a student submission
 * Images are now URL references (/api/py/images/IMAGE_ID), not base64
 */
export async function storeSubmission(
  problemSetId: string,
  problemId: number,
  studentName: string,
  solution: string
): Promise<any> {
  const response = await post<{ success: boolean; submission_id: string; submission: any }>(
    `${API_BASE}/submissions`,
    {
      problem_set_id: problemSetId,
      problem_id: problemId,
      student_name: studentName,
      solution: solution  // Contains image URLs like ![](/ api/py/images/img_123)
    }
  );
  return response.submission;
}

/**
 * Get all submissions for a problem set
 */
export async function getSubmissions(
  problemSetId: string,
  problemId?: number
): Promise<any[]> {
  try {
    const url = problemId
      ? `${API_BASE}/submissions/${problemSetId}?problem_id=${problemId}`
      : `${API_BASE}/submissions/${problemSetId}`;

    const response = await get<{ success: boolean; submissions: any[] }>(url);
    return response.submissions || [];
  } catch (error) {
    console.error('Error fetching submissions:', error);
    return [];
  }
}

/**
 * Get a student's submission for a specific problem
 */
export async function getStudentSubmission(
  problemSetId: string,
  problemId: number,
  studentName: string
): Promise<any | null> {
  try {
    const response = await get<{ success: boolean; submissions: any[] }>(
      `${API_BASE}/submissions/${problemSetId}/${studentName}`
    );
    const submission = response.submissions.find((s: any) => s.problem_id === problemId);
    return submission || null;
  } catch (error) {
    console.error('Error fetching student submission:', error);
    return null;
  }
}

/**
 * Update a submission with grade
 */
export async function updateSubmissionGrade(
  problemSetId: string,
  problemId: number,
  studentName: string,
  grade: any
): Promise<void> {
  // First, get the submission ID
  const submissions = await getSubmissions(problemSetId, problemId);
  const submission = submissions.find(s => s.student_name === studentName);

  if (submission) {
    await put(
      `${API_BASE}/submissions/${submission.id}/grade`,
      grade
    );
  }
}

/**
 * Grade all submissions for a specific problem
 */
export async function gradeBatchForProblem(
  problemSetId: string,
  problemId: number
): Promise<{ success: boolean; statistics: any; results: any[] }> {
  return await post<{ success: boolean; statistics: any; results: any[] }>(
    `${API_BASE}/submissions/grade-batch?problem_set_id=${problemSetId}&problem_id=${problemId}`,
    {}
  );
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get all submissions for a problem set (all problems)
 */
export async function getAllSubmissionsForSet(problemSetId: string): Promise<any[]> {
  return await getSubmissions(problemSetId);
}

/**
 * Count submissions for a problem set
 */
export async function countSubmissions(problemSetId: string): Promise<{
  total: number;
  graded: number;
  byProblem: { [problemId: number]: { total: number; graded: number } };
}> {
  const allSubs = await getAllSubmissionsForSet(problemSetId);
  const graded = allSubs.filter(s => s.graded).length;

  // Count by problem
  const byProblem: { [problemId: number]: { total: number; graded: number } } = {};
  allSubs.forEach(sub => {
    const probId = sub.problem_id;
    if (!byProblem[probId]) {
      byProblem[probId] = { total: 0, graded: 0 };
    }
    byProblem[probId].total++;
    if (sub.graded) {
      byProblem[probId].graded++;
    }
  });

  return {
    total: allSubs.length,
    graded,
    byProblem,
  };
}
