'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { gradeSubmissions, getGradeLetter, getGradeColor } from '@/lib/api';
import { getProblemSet, getSubmissions, updateSubmissionGrade } from '@/lib/api/submissions';
import type { GradingResult } from '@/lib/types';

/**
 * Professor Submissions Grading Page
 * View and grade student submissions
 */
export default function SubmissionsPage() {
  const params = useParams();
  const router = useRouter();
  const setId = params.setId as string;

  // State
  const [problemSet, setProblemSet] = useState<any>(null);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedProblem, setSelectedProblem] = useState(1);
  const [grading, setGrading] = useState(false);
  const [gradedResults, setGradedResults] = useState<{ [key: string]: GradingResult }>({});

  // Load problem set and submissions from backend
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);

        // Get problem set from backend
        const problemSetData = await getProblemSet(setId);
        
        if (!problemSetData) {
          throw new Error('Problem set not found');
        }

        setProblemSet({
          id: setId,
          title: problemSetData.title || 'Problem Set',
          problems: problemSetData.problem_set.map((item: any) => item.problem),
          correctSolutions: problemSetData.problem_set.reduce((acc: any, item: any) => {
            acc[item.problem.id] = item.solution;
            return acc;
          }, {}),
        });

        // Load all submissions from backend
        const allSubmissions = await getSubmissions(setId);
        
        const formattedSubmissions = allSubmissions.map((sub: any) => ({
          name: sub.student_name,
          problemId: sub.problem_id,
          solution: sub.solution,
          submitted: sub.submitted_at,
          graded: sub.graded,
          grade: sub.grade,
        }));

        setSubmissions(formattedSubmissions);
      } catch (err: any) {
        console.error('Error loading data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [setId]);

  // Filter submissions by selected problem
  const problemSubmissions = submissions.filter(s => s.problemId === selectedProblem);
  const currentProblem = problemSet?.problems?.find(p => p.id === selectedProblem);

  // Handle grading
  const handleGradeAll = async () => {
    if (!currentProblem) return;

    try {
      setGrading(true);

      const result = await gradeSubmissions(
        currentProblem,
        problemSet?.correctSolutions?.[selectedProblem] || '',
        problemSubmissions.map(s => ({ name: s.name, solution: s.solution }))
      );

      // Store graded results
      const newGradedResults = { ...gradedResults };
      result.results.forEach((res: GradingResult) => {
        const key = `${res.student_name}-${selectedProblem}`;
        newGradedResults[key] = res;
        
        // Update in localStorage
        updateSubmissionGrade(setId, selectedProblem, res.student_name, res);
      });
      setGradedResults(newGradedResults);

      // Mark as graded
      setSubmissions(submissions.map(s => 
        s.problemId === selectedProblem ? { ...s, graded: true } : s
      ));

      alert(`✅ Successfully graded ${result.results.length} submissions!`);
    } catch (error: any) {
      console.error('Grading error:', error);
      alert(`❌ Grading failed: ${error.message}`);
    } finally {
      setGrading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading submissions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error</h3>
        <p className="mt-1">{error}</p>
        <button onClick={() => router.back()} className="btn-primary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  if (!problemSet) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Problem set not found</h3>
        <button onClick={() => router.back()} className="btn-primary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="text-aub-red hover:text-aub-black text-sm font-medium mb-2"
        >
          ← Back to Problem Set
        </button>
        <h1 className="text-3xl font-bold text-aub-black">Grade Submissions</h1>
        <p className="text-gray-600 mt-1">{problemSet?.title}</p>
      </div>

      {/* Problem Selector */}
      <div className="card">
        <h3 className="font-semibold text-aub-black mb-3">Select Problem:</h3>
        <div className="flex gap-2">
          {problemSet?.problems?.map((problem) => {
            const problemSubs = submissions.filter(s => s.problemId === problem.id);
            const gradedCount = problemSubs.filter(s => s.graded).length;

            return (
              <button
                key={problem.id}
                onClick={() => setSelectedProblem(problem.id)}
                className={`px-4 py-2 rounded-aub border transition-colors ${
                  selectedProblem === problem.id
                    ? 'bg-aub-red text-white border-aub-red'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-aub-red'
                }`}
              >
                <div className="font-medium">Problem {problem.id}</div>
                <div className="text-xs mt-1">
                  {gradedCount}/{problemSubs.length} graded
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Problem Info */}
      {currentProblem && (
        <div className="card bg-aub-beige">
          <h3 className="font-semibold text-aub-black mb-2">
            Problem {currentProblem.id}: {currentProblem.statement}
          </h3>
          <div className="flex items-center gap-3 mt-2">
            <span className="badge text-xs capitalize">{currentProblem.difficulty}</span>
            <span className="badge-info text-xs">{currentProblem.topic}</span>
            <span className="text-sm text-gray-600">
              {problemSubmissions.length} submissions
            </span>
          </div>
        </div>
      )}

      {/* Grade All Button - PROMINENT */}
      {problemSubmissions.length > 0 && !problemSubmissions.every(s => s.graded) && (
        <div className="card bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 shadow-lg">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">🤖</span>
                <h3 className="text-lg font-bold text-green-900">AI Grading Ready</h3>
              </div>
              <p className="text-sm text-green-800 font-medium">
                {problemSubmissions.length} student {problemSubmissions.length === 1 ? 'submission' : 'submissions'} waiting to be graded
              </p>
              <p className="text-xs text-gray-600 mt-1">
                Our AI will analyze each solution, provide detailed feedback, and assign grades in ~10-30 seconds
              </p>
            </div>
            <button
              onClick={handleGradeAll}
              disabled={grading}
              className="btn-primary text-lg px-8 py-4 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all whitespace-nowrap"
            >
              {grading ? (
                <>
                  <span className="spinner mr-2"></span>
                  Grading...
                </>
              ) : (
                <>
                  <span className="text-xl mr-2">✨</span>
                  Grade All {problemSubmissions.length} Submissions
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* All Graded Message */}
      {problemSubmissions.length > 0 && problemSubmissions.every(s => s.graded) && (
        <div className="card bg-green-50 border border-green-300">
          <div className="flex items-center gap-3">
            <span className="text-3xl">✅</span>
            <div>
              <h3 className="font-semibold text-green-900">All Graded!</h3>
              <p className="text-sm text-green-700">
                All {problemSubmissions.length} submissions for this problem have been graded
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Submissions List */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-aub-black">
          Submissions ({problemSubmissions.length})
        </h2>

        {problemSubmissions.length === 0 && (
          <div className="card text-center py-8 text-gray-500">
            <p>No submissions for this problem yet</p>
          </div>
        )}

        {problemSubmissions.map((submission, index) => {
          const key = `${submission.name}-${selectedProblem}`;
          const gradedResult = gradedResults[key];

          return (
            <div key={index} className="card">
              {/* Submission Header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">{submission.name}</h3>
                  <p className="text-sm text-gray-500">
                    Submitted {new Date(submission.submitted).toLocaleDateString()}
                  </p>
                </div>
                {submission.graded && gradedResult && (
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${getGradeColor(gradedResult.evaluation.percentage)}`}>
                      {gradedResult.evaluation.percentage}%
                    </div>
                    <div className="text-sm text-gray-600">
                      {gradedResult.summary.score}/{gradedResult.summary.max_score} points
                    </div>
                  </div>
                )}
              </div>

              {/* Student Solution */}
              <div className="mb-3 p-3 bg-gray-50 rounded-aub border border-gray-200">
                <h4 className="text-xs font-semibold text-gray-700 mb-2">Student Solution:</h4>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{submission.solution}</p>
              </div>

              {/* Graded Results */}
              {submission.graded && gradedResult && (
                <div className="space-y-3">
                  {/* Rubric Scores */}
                  <div className="p-3 bg-blue-50 rounded-aub border border-blue-200">
                    <h4 className="text-xs font-semibold text-blue-900 mb-2">Rubric Breakdown:</h4>
                    <div className="space-y-2">
                      {gradedResult.evaluation.criteria_scores.map((criterion, i) => (
                        <div key={i} className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">{criterion.criterion}</span>
                          <div className="flex items-center gap-2">
                            <span className={criterion.correct ? 'text-green-600' : 'text-orange-600'}>
                              {criterion.earned}/{criterion.possible}
                            </span>
                            <span>{criterion.correct ? '✓' : '○'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Feedback */}
                  <div className="p-3 bg-green-50 rounded-aub border border-green-200">
                    <h4 className="text-xs font-semibold text-green-900 mb-2">Feedback:</h4>
                    
                    {gradedResult.evaluation.strengths.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs font-medium text-green-800">Strengths:</p>
                        <ul className="list-disc pl-5 text-sm text-green-700">
                          {gradedResult.evaluation.strengths.map((strength, i) => (
                            <li key={i}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {gradedResult.evaluation.errors.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-orange-800">Areas for Improvement:</p>
                        <ul className="list-disc pl-5 text-sm text-orange-700">
                          {gradedResult.evaluation.errors.map((error, i) => (
                            <li key={i}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <p className="text-sm text-gray-700 mt-2 pt-2 border-t border-green-300">
                      {gradedResult.evaluation.overall_assessment}
                    </p>
                  </div>
                </div>
              )}

              {!submission.graded && (
                <div className="text-center py-2 text-gray-500 text-sm">
                  Not graded yet - use "Grade All Submissions" button above
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

