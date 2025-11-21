// User Types
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'professor' | 'student';
  avatar?: string;
}

// Material Types
export interface Material {
  doc_id: string;
  chunk_count: number;
  total_chars: number;
  avg_chunk_size: number;
  uploaded_at?: string;
}

export interface Chunk {
  chunk_id: string;
  doc_id: string;
  formatted: string;
  summary: string;
  topics: string[];
  start: number;
  end: number;
  score?: number;
}

// Problem Set Types
export interface Problem {
  id: number;
  difficulty: 'easy' | 'medium' | 'hard';
  topic: string;
  statement: string;
  given: string[];
  required: string[];
}

export interface ProblemQuality {
  overall_quality: 'excellent' | 'good' | 'needs_improvement';
  issues: string[];
  suggestions: string[];
}

export interface ProblemSetItem {
  problem: Problem;
  solution: string;
  quality?: ProblemQuality;
}

export interface ProblemSetAnalysis {
  topics: string[];
  key_formulas: string[];
  concepts: string[];
  difficulty_areas: {
    easy: string[];
    medium: string[];
    hard: string[];
  };
}

export interface ProblemSet {
  id: string;
  doc_id: string;
  analysis: ProblemSetAnalysis;
  num_problems: number;
  problem_set: ProblemSetItem[];
  created_at: string;
  pdf_url?: string;
}

// Submission Types
export interface Submission {
  id: string;
  student_id: string;
  student_name: string;
  problem_set_id: string;
  problem_id: number;
  solution: string;
  submitted_at: string;
  graded: boolean;
  grade?: GradingResult;
}

export interface RubricCriterion {
  step: string;
  points: number;
  requirements: string[];
  partial_credit?: Record<string, number>;
}

export interface Rubric {
  total_points: number;
  criteria: RubricCriterion[];
}

export interface CriterionScore {
  criterion: string;
  earned: number;
  possible: number;
  correct: boolean;
  notes: string;
}

export interface Evaluation {
  score: number;
  max_score: number;
  percentage: number;
  criteria_scores: CriterionScore[];
  strengths: string[];
  errors: string[];
  overall_assessment: string;
}

export interface GradingResult {
  student_name: string;
  problem: Problem;
  rubric: Rubric;
  evaluation: Evaluation;
  feedback: string;
  summary: {
    score: number;
    max_score: number;
    percentage: number;
    grade: string;
  };
}

export interface GradingStatistics {
  total_students: number;
  average: number;
  median: number;
  min: number;
  max: number;
  grade_distribution: Record<string, number>;
}

// Chat/RAG Types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  chunks?: Chunk[];
}

export interface RAGResponse {
  success: boolean;
  prompt: string;
  answer: string;
  retrieved_chunks: Chunk[];
}

// Analytics Types
export interface PerformanceData {
  problem_set_id: string;
  problem_set_name: string;
  average_score: number;
  total_submissions: number;
  graded_submissions: number;
}

export interface ErrorPattern {
  error_type: string;
  frequency: number;
  affected_students: number;
  common_problems: string[];
}

export interface Analytics {
  overall_average: number;
  total_submissions: number;
  total_students: number;
  performance_by_set: PerformanceData[];
  common_errors: ErrorPattern[];
  grade_distribution: Record<string, number>;
  trends: {
    dates: string[];
    averages: number[];
  };
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadResponse {
  success: boolean;
  doc_id: string;
  chunk_count: number;
  chunks: Chunk[];
}

export interface ChunksResponse {
  doc_id: string;
  chunk_count: number;
  chunks: Chunk[];
}

export interface GenerateProblemSetRequest {
  doc_id: string;
  num_problems: number;
  check_quality: boolean;
}

export interface GenerateProblemSetResponse {
  success: boolean;
  problem_set: ProblemSet;
}

export interface GradeSubmissionsRequest {
  problem: Problem;
  correct_solution: string;
  student_submissions: Array<{
    name: string;
    solution: string;
  }>;
}

export interface GradeSubmissionsResponse {
  success: boolean;
  statistics: GradingStatistics;
  results: GradingResult[];
}

export interface RAGQueryRequest {
  query: string;
  doc_id?: string;
  top_k?: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  doc_ids?: string[];
}

export interface SearchResponse {
  success: boolean;
  query: string;
  total_results: number;
  results: Chunk[];
}

// UI State Types
export interface UploadProgress {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
}

export interface GenerationProgress {
  status: 'idle' | 'analyzing' | 'generating' | 'checking' | 'complete' | 'error';
  current_step: string;
  progress: number;
  error?: string;
}

export interface GradingProgress {
  total: number;
  completed: number;
  current_student?: string;
  status: 'idle' | 'grading' | 'complete' | 'error';
  error?: string;
}

// Filter and Sort Types
export interface MaterialFilters {
  search: string;
  sort_by: 'name' | 'date' | 'size';
  sort_order: 'asc' | 'desc';
}

export interface ProblemSetFilters {
  search: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  status?: 'draft' | 'published';
  sort_by: 'date' | 'name' | 'problems';
  sort_order: 'asc' | 'desc';
}

export interface SubmissionFilters {
  search: string;
  graded?: boolean;
  grade_range?: [number, number];
  sort_by: 'date' | 'name' | 'grade';
  sort_order: 'asc' | 'desc';
}

