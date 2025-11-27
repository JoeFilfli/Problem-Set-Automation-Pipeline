/**
 * Course Feedback API Client
 * Handles student feedback submission and retrieval
 */

import { get, post, del } from './client';
import type { CourseFeedbackCreate, CourseFeedback, FeedbackSummary } from '../types';

/**
 * Submit course feedback
 */
export async function submitFeedback(
  data: CourseFeedbackCreate
): Promise<{ success: boolean; feedback_id: string; message: string }> {
  return await post('/api/feedback/submit', data);
}

/**
 * Get current student's feedback
 */
export async function getMyFeedback(
  studentId: string = 'student'
): Promise<CourseFeedback[]> {
  const response = await get<{
    success: boolean;
    total: number;
    feedback: CourseFeedback[];
  }>(`/api/feedback/my-feedback?student_id=${studentId}`);
  return response.feedback;
}

/**
 * Get all feedback (professor view)
 */
export async function getAllFeedback(): Promise<CourseFeedback[]> {
  const response = await get<{
    success: boolean;
    total: number;
    feedback: CourseFeedback[];
  }>('/api/feedback/all');
  return response.feedback;
}

/**
 * Get feedback summary with statistics
 */
export async function getFeedbackSummary(): Promise<FeedbackSummary> {
  return await get<FeedbackSummary>('/api/feedback/summary');
}

/**
 * Delete feedback entry
 */
export async function deleteFeedback(feedbackId: string): Promise<void> {
  await del<{ success: boolean; message: string }>(
    `/api/feedback/feedback/${feedbackId}`
  );
}

