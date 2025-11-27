/**
 * Beat the AI API Client
 * Handles all API calls for the Beat the AI challenge feature
 */

import { get, post, patch, del } from './client';
import type {
  BeatAIChallenge,
  BeatAIChallengeStudent,
  BeatAISubmission,
  BeatAIChallengeCreate,
  BeatAIChallengeUpdate,
  BeatAISubmissionCreate,
  BeatAISubmissionGrade,
  GenerateProblemFromChapterRequest,
  GeneratedProblemContent,
} from '../types';

// ============================================================================
// GENERATION API CALLS
// ============================================================================

/**
 * Generate complete challenge from a chapter (problem + wrong solution + saves it)
 */
export async function generateChallengeFromChapter(
  request: GenerateProblemFromChapterRequest
): Promise<BeatAIChallenge> {
  const response = await post<{
    success: boolean;
    challenge_id: string;
    challenge: BeatAIChallenge;
    message: string;
  }>('/api/beat-ai/generate-challenge-from-chapter', request);
  return response.challenge;
}

/**
 * Generate problem content from a chapter (for manual editing before creating)
 */
export async function generateProblemFromChapter(
  request: GenerateProblemFromChapterRequest
): Promise<GeneratedProblemContent> {
  const response = await post<{
    success: boolean;
    generated: GeneratedProblemContent;
    chapter_id: string;
  }>('/api/beat-ai/generate-problem-from-chapter', request);
  return response.generated;
}

/**
 * Get list of available chapters
 */
export async function getAvailableChapters(): Promise<string[]> {
  const response = await get<{
    chapters: string[];
  }>('/api/py/chapters');
  return response.chapters;
}

// ============================================================================
// PROFESSOR API CALLS
// ============================================================================

/**
 * Create a new Beat the AI challenge
 */
export async function createChallenge(
  data: BeatAIChallengeCreate
): Promise<BeatAIChallenge> {
  const response = await post<{
    success: boolean;
    challenge_id: string;
    challenge: BeatAIChallenge;
  }>('/api/beat-ai/challenges', data);
  return response.challenge;
}

/**
 * Update an existing challenge
 */
export async function updateChallenge(
  challengeId: string,
  data: BeatAIChallengeUpdate
): Promise<BeatAIChallenge> {
  const response = await patch<{
    success: boolean;
    challenge: BeatAIChallenge;
  }>(`/api/beat-ai/challenges/${challengeId}`, data);
  return response.challenge;
}

/**
 * Get all challenges created by the current professor
 */
export async function getMyChallenges(
  createdBy: string = 'professor'
): Promise<BeatAIChallenge[]> {
  const response = await get<{
    success: boolean;
    total: number;
    challenges: BeatAIChallenge[];
  }>(`/api/beat-ai/challenges/my?created_by=${createdBy}`);
  return response.challenges;
}

/**
 * Get a specific challenge (professor view with reference solution)
 */
export async function getChallengeForProfessor(
  challengeId: string
): Promise<BeatAIChallenge> {
  const response = await get<{
    success: boolean;
    challenge: BeatAIChallenge;
  }>(`/api/beat-ai/challenges/${challengeId}/professor`);
  return response.challenge;
}

/**
 * Generate a wrong AI solution for a challenge
 */
export async function generateWrongSolution(
  challengeId: string
): Promise<{ ai_wrong_solution: string; challenge: BeatAIChallenge }> {
  const response = await post<{
    success: boolean;
    ai_wrong_solution: string;
    challenge: BeatAIChallenge;
  }>(`/api/beat-ai/challenges/${challengeId}/generate-wrong-solution`, {});
  return {
    ai_wrong_solution: response.ai_wrong_solution,
    challenge: response.challenge,
  };
}

/**
 * Get all submissions for a specific challenge
 */
export async function getChallengeSubmissions(
  challengeId: string
): Promise<BeatAISubmission[]> {
  const response = await get<{
    success: boolean;
    challenge_id: string;
    total: number;
    submissions: BeatAISubmission[];
  }>(`/api/beat-ai/challenges/${challengeId}/submissions`);
  return response.submissions;
}

/**
 * Grade a submission
 */
export async function gradeSubmission(
  submissionId: string,
  grade: BeatAISubmissionGrade
): Promise<BeatAISubmission> {
  const response = await patch<{
    success: boolean;
    submission_id: string;
    submission: BeatAISubmission;
  }>(`/api/beat-ai/submissions/${submissionId}/grade`, grade);
  return response.submission;
}

/**
 * Delete a challenge and all its submissions
 */
export async function deleteChallenge(challengeId: string): Promise<void> {
  await del<{ success: boolean; message: string }>(
    `/api/beat-ai/challenges/${challengeId}`
  );
}

// ============================================================================
// STUDENT API CALLS
// ============================================================================

/**
 * Get all available challenges for students
 */
export async function getAvailableChallenges(): Promise<
  BeatAIChallengeStudent[]
> {
  const response = await get<{
    success: boolean;
    total: number;
    challenges: BeatAIChallengeStudent[];
  }>('/api/beat-ai/challenges/available');
  return response.challenges;
}

/**
 * Get a specific challenge (student view without reference solution)
 */
export async function getChallenge(
  challengeId: string
): Promise<BeatAIChallengeStudent> {
  const response = await get<{
    success: boolean;
    challenge: BeatAIChallengeStudent;
  }>(`/api/beat-ai/challenges/${challengeId}`);
  return response.challenge;
}

/**
 * Submit a solution to a challenge
 */
export async function submitSolution(
  data: BeatAISubmissionCreate
): Promise<BeatAISubmission> {
  const response = await post<{
    success: boolean;
    submission_id: string;
    submission: BeatAISubmission;
  }>(`/api/beat-ai/challenges/${data.challenge_id}/submissions`, data);
  return response.submission;
}

/**
 * Get the current student's submission for a challenge
 */
export async function getMySubmission(
  challengeId: string,
  studentId: string = 'student'
): Promise<BeatAISubmission | null> {
  const response = await get<{
    success: boolean;
    challenge_id: string;
    submission: BeatAISubmission | null;
  }>(`/api/beat-ai/challenges/${challengeId}/submissions/my?student_id=${studentId}`);
  return response.submission;
}

/**
 * Get the reference solution for a challenge (only after submitting)
 */
export async function getReferenceSolution(
  challengeId: string,
  studentId: string = 'student'
): Promise<string> {
  const response = await get<{
    success: boolean;
    reference_solution: string;
  }>(`/api/beat-ai/challenges/${challengeId}/reference-solution?student_id=${studentId}`);
  return response.reference_solution;
}

