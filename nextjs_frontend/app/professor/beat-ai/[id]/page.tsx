'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getChallengeForProfessor,
  generateWrongSolution,
  getChallengeSubmissions,
  gradeSubmission,
  updateChallenge,
} from '@/lib/api/beatAi';
import type { BeatAIChallenge, BeatAISubmission } from '@/lib/types';
import MarkdownRenderer from '@/components/MarkdownRenderer';

/**
 * Beat the AI Challenge Detail Page (Professor View)
 * View challenge details, edit, generate wrong solution, and grade submissions
 */
export default function ChallengeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const challengeId = params.id as string;

  // State
  const [challenge, setChallenge] = useState<BeatAIChallenge | null>(null);
  const [submissions, setSubmissions] = useState<BeatAISubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedSolution, setEditedSolution] = useState('');

  // Selected submission for grading
  const [selectedSubmission, setSelectedSubmission] = useState<BeatAISubmission | null>(null);
  const [gradeScore, setGradeScore] = useState('');
  const [gradeNotes, setGradeNotes] = useState('');
  const [grading, setGrading] = useState(false);

  // Load challenge and submissions
  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [challengeId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [challengeData, submissionsData] = await Promise.all([
        getChallengeForProfessor(challengeId),
        getChallengeSubmissions(challengeId),
      ]);

      setChallenge(challengeData);
      setSubmissions(submissionsData);
      setEditedSolution(challengeData.ai_wrong_solution || '');
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.message || 'Failed to load challenge');
    } finally {
      setLoading(false);
    }
  };

  // Generate wrong solution handler
  const handleGenerateWrongSolution = async () => {
    if (!confirm('Generate a new AI wrong solution? This will replace the existing one.')) {
      return;
    }

    try {
      setGenerating(true);
      const result = await generateWrongSolution(challengeId);
      setChallenge(result.challenge);
      setEditedSolution(result.ai_wrong_solution);
      alert('AI wrong solution generated successfully!');
    } catch (err: any) {
      console.error('Error generating wrong solution:', err);
      alert('Failed to generate wrong solution: ' + err.message);
    } finally {
      setGenerating(false);
    }
  };

  // Save edited AI solution
  const handleSaveAISolution = async () => {
    try {
      const updated = await updateChallenge(challengeId, {
        ai_wrong_solution: editedSolution,
      });
      setChallenge(updated);
      setEditMode(false);
      alert('AI solution updated successfully!');
    } catch (err: any) {
      console.error('Error updating solution:', err);
      alert('Failed to update solution: ' + err.message);
    }
  };

  // Open grading modal
  const openGradingModal = (submission: BeatAISubmission) => {
    setSelectedSubmission(submission);
    setGradeScore(submission.score?.toString() || '');
    setGradeNotes(submission.review_notes || '');
  };

  // Submit grade
  const handleSubmitGrade = async () => {
    if (!selectedSubmission) return;

    const score = parseFloat(gradeScore);
    if (isNaN(score) || score < 0 || score > 100) {
      alert('Please enter a valid score between 0 and 100');
      return;
    }

    try {
      setGrading(true);
      const updated = await gradeSubmission(selectedSubmission.id, {
        score,
        review_notes: gradeNotes,
      });

      // Update submissions list
      setSubmissions(prev =>
        prev.map(s => (s.id === updated.id ? updated : s))
      );

      // Close modal
      setSelectedSubmission(null);
      setGradeScore('');
      setGradeNotes('');
    } catch (err: any) {
      console.error('Error grading submission:', err);
      alert('Failed to grade submission: ' + err.message);
    } finally {
      setGrading(false);
    }
  };

  // Get difficulty badge color
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'EASY': return 'bg-green-100 text-green-800';
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
      case 'HARD': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading challenge...</p>
        </div>
      </div>
    );
  }

  if (error || !challenge) {
    return (
      <div className="card bg-red-50 border-red-200">
        <p className="text-red-800">{error || 'Challenge not found'}</p>
        <button onClick={() => router.back()} className="btn-secondary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-aub-black">{challenge.title}</h1>
            <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyColor(challenge.difficulty)}`}>
              {challenge.difficulty}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 mb-2">
            {challenge.tags.map((tag, i) => (
              <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                {tag}
              </span>
            ))}
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-medium">Chapter:</span> {challenge.chapter_id}
            {challenge.topic && (
              <>
                {' '}<span className="text-gray-400">•</span>{' '}
                <span className="font-medium">Topic:</span> {challenge.topic}
              </>
            )}
          </div>
        </div>
        <button onClick={() => router.back()} className="btn-secondary">
          ← Back
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm text-gray-600">Total Submissions</div>
          <div className="text-2xl font-bold text-aub-black mt-1">
            {submissions.length}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600">Graded</div>
          <div className="text-2xl font-bold text-aub-black mt-1">
            {submissions.filter(s => s.score !== null && s.score !== undefined).length}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-600">Avg Score</div>
          <div className="text-2xl font-bold text-aub-black mt-1">
            {challenge.avg_score ? `${challenge.avg_score.toFixed(1)}%` : '-'}
          </div>
        </div>
      </div>

      {/* Problem Statement */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">Problem Statement</h2>
        <MarkdownRenderer content={challenge.problem_statement} />
      </div>

      {/* AI Wrong Solution */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-aub-black">AI Wrong Solution</h2>
          <div className="flex gap-2">
            <button
              onClick={handleGenerateWrongSolution}
              className="btn-secondary"
              disabled={generating}
            >
              {generating ? (
                <>
                  <span className="spinner mr-2"></span>
                  Generating...
                </>
              ) : (
                '🤖 Generate AI Solution'
              )}
            </button>
            {!editMode && challenge.ai_wrong_solution && (
              <button
                onClick={() => setEditMode(true)}
                className="btn-secondary"
              >
                ✏️ Edit
              </button>
            )}
          </div>
        </div>

        {editMode ? (
          <div className="space-y-4">
            <textarea
              value={editedSolution}
              onChange={(e) => setEditedSolution(e.target.value)}
              rows={12}
              className="input-primary w-full font-mono text-sm"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setEditMode(false);
                  setEditedSolution(challenge.ai_wrong_solution || '');
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button onClick={handleSaveAISolution} className="btn-primary">
                Save
              </button>
            </div>
          </div>
        ) : challenge.ai_wrong_solution ? (
          <div className="bg-gray-50 p-4 rounded-aub">
            <MarkdownRenderer content={challenge.ai_wrong_solution} />
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-aub">
            <p>No AI solution generated yet.</p>
            <p className="text-sm mt-1">Click &quot;Generate AI Solution&quot; to create one automatically.</p>
          </div>
        )}
      </div>

      {/* Reference Solution */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">Reference Solution</h2>
        <div className="bg-green-50 p-4 rounded-aub">
          <MarkdownRenderer content={challenge.reference_solution} />
        </div>
      </div>

      {/* Submissions */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Student Submissions ({submissions.length})
        </h2>

        {submissions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No submissions yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {submissions.map((submission) => (
              <div
                key={submission.id}
                className="border border-gray-200 rounded-aub p-4 hover:border-aub-red transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="font-semibold text-gray-900">
                      Student: {submission.student_id}
                    </div>
                    <div className="text-sm text-gray-500">
                      Submitted: {new Date(submission.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {submission.score !== null && submission.score !== undefined ? (
                      <span className="px-3 py-1 bg-green-100 text-green-800 rounded font-semibold">
                        {submission.score}%
                      </span>
                    ) : (
                      <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded">
                        Not graded
                      </span>
                    )}
                    <button
                      onClick={() => openGradingModal(submission)}
                      className="btn-secondary text-sm"
                    >
                      Grade
                    </button>
                  </div>
                </div>

                <div className="space-y-4 text-sm">
                  {/* Selected Errors */}
                  <div>
                    <div className="font-medium text-gray-700 mb-2">
                      Selected Errors ({submission.selected_errors?.length || 0})
                    </div>
                    <div className="space-y-2">
                      {submission.selected_errors?.map((err: any, idx: number) => {
                        const errorTypeLabels: Record<string, { label: string; color: string }> = {
                          'incorrect_calculation': { label: 'Incorrect Calculation', color: 'bg-red-100 text-red-800' },
                          'unnecessary_step': { label: 'Unnecessary Step', color: 'bg-orange-100 text-orange-800' },
                          'logic_error': { label: 'Logic Error', color: 'bg-purple-100 text-purple-800' },
                          'custom': { label: 'Custom', color: 'bg-gray-100 text-gray-800' },
                        };
                        const typeDisplay = errorTypeLabels[err.error_type] || errorTypeLabels['logic_error'];
                        
                        return (
                          <div key={idx} className="border border-gray-200 rounded-aub p-3">
                            <div className="flex items-start gap-2 mb-2">
                              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-bold">
                                {err.segment_index}
                              </div>
                              <div className="flex-1">
                                <div className="bg-red-50 p-2 rounded text-red-900 font-mono text-xs mb-2">
                                  {err.segment_text}
                                </div>
                                <span className={`px-2 py-1 text-xs font-semibold rounded ${typeDisplay.color}`}>
                                  {typeDisplay.label}
                                </span>
                                {err.error_type === 'custom' && err.custom_description && (
                                  <div className="mt-2 text-gray-700">
                                    <span className="font-medium">Description:</span> {err.custom_description}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Workflow Suggestion */}
                  {submission.workflow_suggestion && (
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Workflow Suggestion</div>
                      <div className="bg-blue-50 p-2 rounded text-gray-700">
                        {submission.workflow_suggestion}
                      </div>
                    </div>
                  )}

                  {/* AI Feedback */}
                  {(submission as any).ai_feedback && (
                    <div>
                      <div className="font-medium text-gray-700 mb-1">AI Feedback (Instant)</div>
                      <div className="bg-purple-50 p-2 rounded text-gray-700 text-sm">
                        {(submission as any).ai_feedback}
                      </div>
                    </div>
                  )}

                  {/* Review Notes */}
                  {submission.review_notes && (
                    <div>
                      <div className="font-medium text-gray-700 mb-1">Your Review Notes</div>
                      <div className="bg-yellow-50 p-2 rounded text-gray-700">
                        {submission.review_notes}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Grading Modal */}
      {selectedSubmission && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-aub p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold text-aub-black mb-4">
              Grade Submission
            </h2>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Score (0-100) *
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={gradeScore}
                  onChange={(e) => setGradeScore(e.target.value)}
                  className="input-primary w-full"
                  placeholder="Enter score..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Review Notes
                </label>
                <textarea
                  value={gradeNotes}
                  onChange={(e) => setGradeNotes(e.target.value)}
                  rows={4}
                  className="input-primary w-full"
                  placeholder="Add feedback for the student..."
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setSelectedSubmission(null);
                  setGradeScore('');
                  setGradeNotes('');
                }}
                className="btn-secondary"
                disabled={grading}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitGrade}
                className="btn-primary"
                disabled={grading}
              >
                {grading ? (
                  <>
                    <span className="spinner mr-2"></span>
                    Grading...
                  </>
                ) : (
                  'Submit Grade'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

