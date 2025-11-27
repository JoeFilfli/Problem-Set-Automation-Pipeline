'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import {
  getProblemSet,
  storeSubmission,
  getStudentSubmission
} from '@/lib/api/submissions';
import MarkdownEditor from '@/components/MarkdownEditor';

/**
 * Student Problem Set View
 * View problems and submit solutions
 */
export default function StudentProblemSetPage() {
  const params = useParams();
  const router = useRouter();
  const setId = params.setId as string;
  const studentName = 'Current Student'; // In production, get from auth context

  // State
  const [problemSet, setProblemSet] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Submission state
  const [submissions, setSubmissions] = useState<{ [key: number]: string }>({});
  const [submittedProblems, setSubmittedProblems] = useState<Set<number>>(new Set());
  const [showSolutions, setShowSolutions] = useState<Set<number>>(new Set());
  const [submissionData, setSubmissionData] = useState<{ [key: number]: any }>({});
  const [feedbackTab, setFeedbackTab] = useState<{ [key: number]: string }>({});

  // Load problem set and existing submissions
  useEffect(() => {
    async function loadProblemSet() {
      try {
        setLoading(true);
        setError(null);

        // Get problem set from backend
        const problemSetData = await getProblemSet(setId);

        if (!problemSetData) {
          setError('Problem set not found');
          setLoading(false);
          return;
        }

        setProblemSet(problemSetData);

        // Load existing submissions
        const submitted = new Set<number>();
        const existingSubmissions: { [key: number]: string } = {};
        const submissionDetails: { [key: number]: any } = {};

        for (const item of problemSetData.problem_set) {
          const problemId = item.problem.id;
          const existing = await getStudentSubmission(setId, problemId, studentName);
          if (existing) {
            submitted.add(problemId);
            // Solution already contains image URLs - no reconstruction needed
            existingSubmissions[problemId] = existing.solution || '';
            submissionDetails[problemId] = existing; // Store full submission data including grade
          }
        }

        setSubmittedProblems(submitted);
        setSubmissions(existingSubmissions);
        setSubmissionData(submissionDetails);
      } catch (err: any) {
        console.error('Error loading problem set:', err);
        setError(err.message || 'Failed to load problem set');
      } finally {
        setLoading(false);
      }
    }

    loadProblemSet();
  }, [setId, studentName]);

  // Handle submission
  const handleSubmit = async (problemId: number) => {
    if (!submissions[problemId]?.trim()) {
      alert('Please write your solution before submitting');
      return;
    }

    try {
      // Store submission via backend
      await storeSubmission(setId, problemId, studentName, submissions[problemId]);

      // Mark as submitted
      setSubmittedProblems(new Set([...Array.from(submittedProblems), problemId]));
      alert('Solution submitted successfully! Your professor will grade it soon.');
    } catch (error: any) {
      alert(`Failed to submit: ${error.message}`);
    }
  };

  // Toggle solution visibility
  const toggleSolution = (problemId: number) => {
    const newShowSolutions = new Set(showSolutions);
    if (newShowSolutions.has(problemId)) {
      newShowSolutions.delete(problemId);
    } else {
      newShowSolutions.add(problemId);
    }
    setShowSolutions(newShowSolutions);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading problem set...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error loading problem set</h3>
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
        <p className="mt-1">This problem set may not exist or has been removed.</p>
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
          ← Back to Problem Sets
        </button>
        <h1 className="text-3xl font-bold text-aub-black">{problemSet.title}</h1>
        <p className="text-gray-600 mt-1">
          {problemSet.num_problems} problems · Due in 5 days
        </p>
      </div>

      {/* Progress Banner */}
      <div className="card bg-aub-red-pale">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-aub-black">Your Progress</h3>
          <span className="text-sm font-medium text-aub-black">
            {submittedProblems.size} / {problemSet.num_problems} submitted
          </span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill bg-aub-red"
            style={{
              width: `${(submittedProblems.size / problemSet.num_problems) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Problems */}
      <div className="space-y-6">
        {problemSet.problem_set.map((item: any, index: number) => {
          const problem = item.problem;
          const solution = item.solution;
          const isSubmitted = submittedProblems.has(problem.id);
          const showingSolution = showSolutions.has(problem.id);
          const submissionInfo = submissionData[problem.id];
          const isGraded = submissionInfo?.graded;
          const grade = submissionInfo?.grade;
          const percentage = grade?.summary?.percentage ?? 0;
          const letterGrade = grade?.summary?.grade ?? 'Graded';
          const criteriaScores = grade?.evaluation?.criteria_scores || [];
          const totalCriteria = criteriaScores.length;
          const correctCriteria = criteriaScores.filter((criterion: any) => criterion.correct).length;
          const strengthsList = grade?.evaluation?.strengths || [];
          const improvementList = grade?.evaluation?.errors || [];
          const scoreLine = grade?.summary ? `${grade.summary.score}/${grade.summary.max_score} points` : 'Score available';
          const toneKey = percentage >= 90 ? 'green' : percentage >= 80 ? 'blue' : percentage >= 70 ? 'amber' : 'orange';
          const tone = {
            green: { border: 'border-green-500', header: 'from-green-700 to-emerald-500' },
            blue: { border: 'border-blue-500', header: 'from-blue-700 to-sky-500' },
            amber: { border: 'border-amber-500', header: 'from-amber-700 to-orange-500' },
            orange: { border: 'border-orange-600', header: 'from-orange-700 to-amber-500' },
          }[toneKey];

          return (
            <div key={problem.id} className="card">
              {/* Problem Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-bold text-aub-black">
                      Problem {index + 1}
                    </h2>
                    {isSubmitted && (
                      <span className="badge-success">Submitted</span>
                    )}
                    <span className="badge text-xs capitalize">
                      {problem.difficulty}
                    </span>
                    <span className="badge-info text-xs">
                      {problem.topic}
                    </span>
                  </div>
                  <p className="text-lg text-gray-800">{problem.statement}</p>
                </div>
              </div>

              {/* Given Information */}
              {problem.given && problem.given.length > 0 && (
                <div className="mb-4 p-4 bg-aub-beige rounded-aub">
                  <h3 className="text-sm font-semibold text-aub-black mb-2">
                    Given:
                  </h3>
                  <ul className="space-y-1">
                    {problem.given.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700">
                        • {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Required */}
              {problem.required && problem.required.length > 0 && (
                <div className="mb-4 p-4 bg-blue-50 rounded-aub border border-blue-200">
                  <h3 className="text-sm font-semibold text-blue-900 mb-2">
                    Required:
                  </h3>
                  <ul className="space-y-1">
                    {problem.required.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-blue-800">
                        • {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Solution Input */}
              <div className="mb-4">
                <label className="label">Your Solution:</label>
                <MarkdownEditor
                  value={submissions[problem.id] || ''}
                  onChange={(value) =>
                    setSubmissions({ ...submissions, [problem.id]: value })
                  }
                  placeholder="Write your solution here... You can use markdown formatting, LaTeX math ($x^2$ or $$E=mc^2$$), and upload images!"
                  disabled={isSubmitted}
                  minHeight="350px"
                />
              </div>

              {/* Grading Status */}
              {isGraded && grade && (
                <div className={`mb-4 rounded-aub border-2 overflow-hidden ${grade.summary?.percentage >= 90 ? 'border-green-500' :
                  grade.summary?.percentage >= 80 ? 'border-blue-500' :
                    grade.summary?.percentage >= 70 ? 'border-yellow-500' :
                      'border-orange-500'
                  }`}>
                  {/* Header Section */}
                  <div className={`px-4 py-3 ${grade.summary?.percentage >= 90 ? 'bg-green-50' :
                    grade.summary?.percentage >= 80 ? 'bg-blue-50' :
                      grade.summary?.percentage >= 70 ? 'bg-yellow-50' :
                        'bg-orange-50'
                    }`}>
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                        <span>✅</span>
                        <span>Graded</span>
                      </h3>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-gray-900">
                          {grade.summary?.percentage?.toFixed(0)}%
                        </div>
                        <div className="text-sm text-gray-600">
                          {grade.summary?.score}/{grade.summary?.max_score} points · Grade: {grade.summary?.grade}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Tabs Navigation */}
                  <div className="bg-white border-b border-gray-200">
                    <div className="flex gap-1 px-2 pt-2">
                      {['overview', 'rubric', 'strengths', 'feedback'].map((tab) => {
                        const currentTab = feedbackTab[problem.id] || 'overview';
                        const isActive = currentTab === tab;
                        const labels = {
                          overview: '📊 Overview',
                          rubric: '📋 Rubric',
                          strengths: '💡 Insights',
                          feedback: '💬 Feedback'
                        };

                        return (
                          <button
                            key={tab}
                            onClick={() => setFeedbackTab({ ...feedbackTab, [problem.id]: tab })}
                            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${isActive
                              ? 'bg-white text-aub-red border-t border-x border-gray-200'
                              : 'bg-gray-50 text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                              }`}
                          >
                            {labels[tab as keyof typeof labels]}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Tab Content */}
                  <div className="bg-white px-4 py-4">
                    {/* Overview Tab */}
                    {(!feedbackTab[problem.id] || feedbackTab[problem.id] === 'overview') && (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <div className="text-xs text-gray-600 mb-1">Your Score</div>
                            <div className="text-2xl font-bold text-gray-900">
                              {grade.summary?.score}/{grade.summary?.max_score}
                            </div>
                          </div>
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <div className="text-xs text-gray-600 mb-1">Letter Grade</div>
                            <div className="text-2xl font-bold text-aub-red">
                              {grade.summary?.grade}
                            </div>
                          </div>
                        </div>
                        {grade.evaluation?.criteria_scores && grade.evaluation.criteria_scores.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-gray-900 mb-2 text-sm">Quick Summary:</h4>
                            <div className="flex flex-wrap gap-2">
                              {grade.evaluation.criteria_scores.map((criterion: any, idx: number) => (
                                <span
                                  key={idx}
                                  className={`px-2 py-1 rounded text-xs font-medium ${criterion.correct
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-700'
                                    }`}
                                >
                                  {criterion.correct ? '✓' : '○'} {criterion.criterion}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Rubric Tab */}
                    {feedbackTab[problem.id] === 'rubric' && (
                      <div>
                        {grade.evaluation?.criteria_scores && grade.evaluation.criteria_scores.length > 0 ? (
                          <div className="space-y-2">
                            {grade.evaluation.criteria_scores.map((criterion: any, idx: number) => (
                              <div
                                key={idx}
                                className={`p-3 rounded-lg border ${criterion.correct
                                  ? 'border-green-200 bg-green-50'
                                  : 'border-gray-200 bg-gray-50'
                                  }`}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-lg ${criterion.correct ? 'text-green-600' : 'text-gray-400'}`}>
                                      {criterion.correct ? '✓' : '○'}
                                    </span>
                                    <span className="font-medium text-gray-900">{criterion.criterion}</span>
                                  </div>
                                  <span className="font-bold text-gray-900">
                                    {criterion.earned}/{criterion.possible} pts
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-600 text-sm">No rubric details available.</p>
                        )}
                      </div>
                    )}

                    {/* Strengths & Improvements Tab */}
                    {feedbackTab[problem.id] === 'strengths' && (
                      <div className="space-y-4">
                        {grade.evaluation?.strengths && grade.evaluation.strengths.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
                              <span>✨</span>
                              <span>What You Did Well</span>
                            </h4>
                            <ul className="space-y-2">
                              {grade.evaluation.strengths.map((strength: string, idx: number) => (
                                <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                  <span className="text-green-600 mt-0.5">▪</span>
                                  <span>{strength}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {grade.evaluation?.errors && grade.evaluation.errors.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-orange-900 mb-2 flex items-center gap-2">
                              <span>📝</span>
                              <span>Areas for Improvement</span>
                            </h4>
                            <ul className="space-y-2">
                              {grade.evaluation.errors.map((error: string, idx: number) => (
                                <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                  <span className="text-orange-600 mt-0.5">▪</span>
                                  <span>{error}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {(!grade.evaluation?.strengths || grade.evaluation.strengths.length === 0) &&
                          (!grade.evaluation?.errors || grade.evaluation.errors.length === 0) && (
                            <p className="text-gray-600 text-sm">No detailed insights available.</p>
                          )}
                      </div>
                    )}

                    {/* Detailed Feedback Tab */}
                    {feedbackTab[problem.id] === 'feedback' && (
                      <div>
                        {grade.feedback ? (
                          <div className="prose prose-sm max-w-none text-gray-800 [&_.katex]:text-base [&_.katex-display]:my-4">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm, remarkMath]}
                              rehypePlugins={[rehypeKatex]}
                            >
                              {grade.feedback.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$').replace(/\\\(/g, '$').replace(/\\\)/g, '$')}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="text-gray-600 text-sm">No additional feedback provided.</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3">
                {!isSubmitted ? (
                  <button
                    onClick={() => handleSubmit(problem.id)}
                    className="btn-primary"
                  >
                    Submit Solution
                  </button>
                ) : isGraded ? (
                  <button disabled className="btn-primary opacity-50 cursor-not-allowed">
                    ✓ Graded
                  </button>
                ) : (
                  <button disabled className="btn-secondary opacity-50 cursor-not-allowed">
                    ⏳ Awaiting Grade
                  </button>
                )}

                <button
                  onClick={() => toggleSolution(problem.id)}
                  className="btn-secondary"
                >
                  {showingSolution ? 'Hide Solution' : 'Show Solution'}
                </button>
              </div>

              {/* Solution Display */}
              {showingSolution && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-aub">
                  <h3 className="text-sm font-semibold text-green-900 mb-2">
                    Model Solution:
                  </h3>
                  <div className="prose prose-sm max-w-none text-gray-800">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {solution}
                    </ReactMarkdown>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Submit All Button */}
      {submittedProblems.size < problemSet.num_problems && (
        <div className="card bg-yellow-50 border border-yellow-200">
          <p className="text-sm text-yellow-800">
            💡 <strong>Reminder:</strong> Make sure to submit all problems before the due date!
          </p>
        </div>
      )}
    </div>
  );
}

