/**
 * Analytics API
 * Handles professor analytics and insights
 */

import { get } from './client';

export interface ProblemSetWithSubmissions {
    id: string;
    topic: string;
    submission_count: number;
    last_updated: number;
}

export interface CommonError {
    error: string;
    count: number;
}

export interface CommonStrength {
    strength: string;
    count: number;
}

export interface StudentPerformance {
    student_name: string;
    problem_id: number;
    score: number;
    grade: string;
    submission_id: string;
}

export interface AnalyticsStats {
    total_submissions: number;
    graded_submissions: number;
    average_score: number;
    median_score: number;
    min_score: number;
    max_score: number;
    grade_distribution: Record<string, number>;
    common_errors: CommonError[];
    common_strengths: CommonStrength[];
}

export interface ProblemDifficulty {
    problem_id: number;
    topic: string;
    avg_score: number;
    difficulty: string;
    color: string;
    submission_count: number;
}

export interface Recommendation {
    type: string;
    severity: string;
    title: string;
    description: string;
    problems: string[];
}

export interface LearningGap {
    concept: string;
    description: string;
    frequency: number;
    recommendation: string;
}

export interface CurriculumOptimization {
    problem_difficulty: ProblemDifficulty[];
    recommendations: Recommendation[];
    learning_gaps: LearningGap[];
}

export interface AnalyticsResponse {
    success: boolean;
    problem_set_id: string;
    has_data: boolean;
    message?: string;
    stats?: AnalyticsStats;
    student_performance?: StudentPerformance[];
    curriculum_optimization?: CurriculumOptimization;
}

/**
 * Get list of problem sets that have submissions
 */
export async function getAnalyticsProblemSets(): Promise<{
    success: boolean;
    problem_sets: ProblemSetWithSubmissions[];
}> {
    return get('/api/py/analytics/problem-sets');
}

/**
 * Get aggregated analytics for a problem set
 */
export async function getProblemSetAnalytics(
    problemSetId: string
): Promise<AnalyticsResponse> {
    return get(`/api/py/analytics/${problemSetId}`);
}
