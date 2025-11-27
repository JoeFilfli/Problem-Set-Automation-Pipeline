'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getChallenge,
  getMySubmission,
  submitSolution,
  getReferenceSolution,
} from '@/lib/api/beatAi';
import type { BeatAIChallengeStudent, BeatAISubmission, ErrorClassification } from '@/lib/types';
import MarkdownRenderer from '@/components/MarkdownRenderer';

/**
 * Beat the AI Challenge Page (Student View)
 * Simplified: Select incorrect steps, classify errors, optional workflow suggestion
 */
export default function StudentChallengeWizardPage() {
  const params = useParams();
  const router = useRouter();
  const challengeId = params.id as string;

  // Data state
  const [challenge, setChallenge] = useState<BeatAIChallengeStudent | null>(null);
  const [submission, setSubmission] = useState<BeatAISubmission | null>(null);
  const [referenceSolution, setReferenceSolution] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // AI solution segments
  const [aiSolutionSegments, setAiSolutionSegments] = useState<string[]>([]);

  // Selected errors with classifications
  const [selectedErrors, setSelectedErrors] = useState<ErrorClassification[]>([]);
  
  // Workflow suggestion (optional)
  const [workflowSuggestion, setWorkflowSuggestion] = useState('');

  // UI state
  const [submitting, setSubmitting] = useState(false);

  // Error type options
  const errorTypeOptions = [
    { value: 'incorrect_calculation', label: 'Incorrect Calculation', color: 'bg-red-100 text-red-800' },
    { value: 'unnecessary_step', label: 'Unnecessary Step', color: 'bg-orange-100 text-orange-800' },
    { value: 'logic_error', label: 'Logic Error', color: 'bg-purple-100 text-purple-800' },
    { value: 'custom', label: 'Other (Custom)', color: 'bg-gray-100 text-gray-800' },
  ];

  // Load challenge and check for existing submission
  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [challengeId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [challengeData, submissionData] = await Promise.all([
        getChallenge(challengeId),
        getMySubmission(challengeId),
      ]);

      setChallenge(challengeData);
      setSubmission(submissionData);

      // Split AI solution into segments (non-empty lines)
      if (challengeData.ai_wrong_solution) {
        const segments = challengeData.ai_wrong_solution
          .split('\n')
          .filter(line => line.trim().length > 0);
        setAiSolutionSegments(segments);
      }

      // If submission exists, load reference solution
      if (submissionData) {
        try {
          const refSolution = await getReferenceSolution(challengeId);
          setReferenceSolution(refSolution);
        } catch (err) {
          console.error('Error loading reference solution:', err);
        }
      }
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.message || 'Failed to load challenge');
    } finally {
      setLoading(false);
    }
  };

  // Toggle segment selection
  const handleToggleSegment = (index: number, text: string) => {
    const existingIndex = selectedErrors.findIndex(e => e.segment_index === index);
    
    if (existingIndex >= 0) {
      // Remove this segment
      setSelectedErrors(selectedErrors.filter(e => e.segment_index !== index));
    } else {
      // Add this segment with default error type
      setSelectedErrors([
        ...selectedErrors,
        {
          segment_index: index,
          segment_text: text,
          error_type: 'logic_error',
          custom_description: null,
        }
      ]);
    }
  };

  // Update error classification for a segment
  const handleUpdateErrorType = (segmentIndex: number, errorType: string) => {
    setSelectedErrors(selectedErrors.map(err => 
      err.segment_index === segmentIndex
        ? { ...err, error_type: errorType as ErrorClassification['error_type'], custom_description: errorType === 'custom' ? err.custom_description : null }
        : err
    ));
  };

  // Update custom description for a segment
  const handleUpdateCustomDescription = (segmentIndex: number, description: string) => {
    setSelectedErrors(selectedErrors.map(err => 
      err.segment_index === segmentIndex
        ? { ...err, custom_description: description }
        : err
    ));
  };

  // Get selected error for a segment
  const getSelectedError = (segmentIndex: number): ErrorClassification | undefined => {
    return selectedErrors.find(e => e.segment_index === segmentIndex);
  };

  // Check if segment is selected
  const isSegmentSelected = (segmentIndex: number): boolean => {
    return selectedErrors.some(e => e.segment_index === segmentIndex);
  };

  // Validate submission
  const canSubmit = selectedErrors.length > 0 && selectedErrors.every(err => 
    err.error_type !== 'custom' || (err.custom_description && err.custom_description.trim().length > 0)
  );

  // Submit solution
  const handleSubmit = async () => {
    if (!canSubmit) {
      setError('Please select at least one error and provide descriptions for custom error types');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const submissionData = {
        challenge_id: challengeId,
        selected_errors: selectedErrors,
        workflow_suggestion: workflowSuggestion.trim() || undefined,
      };

      const newSubmission = await submitSolution(submissionData);
      setSubmission(newSubmission);

      // Load reference solution
      try {
        const refSolution = await getReferenceSolution(challengeId);
        setReferenceSolution(refSolution);
      } catch (err) {
        console.error('Error loading reference solution:', err);
      }
    } catch (err: any) {
      console.error('Error submitting solution:', err);
      setError('Failed to submit: ' + err.message);
    } finally {
      setSubmitting(false);
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

  // Get error type label and color
  const getErrorTypeDisplay = (errorType: string) => {
    return errorTypeOptions.find(opt => opt.value === errorType) || errorTypeOptions[2];
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

  if (error && !challenge) {
    return (
      <div className="card bg-red-50 border-red-200">
        <p className="text-red-800">{error}</p>
        <button onClick={() => router.back()} className="btn-secondary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  if (!challenge) {
    return (
      <div className="card bg-red-50 border-red-200">
        <p className="text-red-800">Challenge not found</p>
        <button onClick={() => router.back()} className="btn-secondary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  // If submission exists, show read-only view
  if (submission) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <button onClick={() => router.back()} className="text-aub-red hover:text-aub-black mb-4">
            ← Back to Challenges
          </button>
          <h1 className="text-3xl font-bold text-aub-black">{challenge.title}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyColor(challenge.difficulty)}`}>
              {challenge.difficulty}
            </span>
            <span className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full font-semibold">
              ✓ Submitted
            </span>
          </div>
        </div>

        {/* Score */}
        {submission.score !== null && submission.score !== undefined && (
          <div className="card bg-green-50 border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-green-900">Your Score</h3>
                <p className="text-sm text-green-700 mt-1">
                  Professor&apos;s feedback is available below
                </p>
              </div>
              <div className="text-4xl font-bold text-green-900">
                {submission.score}%
              </div>
            </div>
            {submission.review_notes && (
              <div className="mt-4 pt-4 border-t border-green-200">
                <p className="text-sm font-medium text-green-900 mb-1">Review Notes:</p>
                <p className="text-green-800">{submission.review_notes}</p>
              </div>
            )}
          </div>
        )}

        {/* AI Feedback */}
        {submission.ai_feedback && (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-start gap-3 mb-4">
              <div className="text-3xl">🤖</div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-blue-900 mb-2">AI Feedback</h2>
                <p className="text-sm text-blue-700 mb-3">
                  Here&apos;s what our AI thinks about your error identification:
                </p>
              </div>
            </div>
            <div className="bg-white p-4 rounded-aub border border-blue-200">
              <MarkdownRenderer content={submission.ai_feedback} />
            </div>
          </div>
        )}

        {/* Your Submission */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">Your Submission</h2>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-700 mb-3">
                Selected Errors ({submission.selected_errors.length})
              </h3>
              <div className="space-y-3">
                {submission.selected_errors.map((err, idx) => {
                  const typeDisplay = getErrorTypeDisplay(err.error_type);
                  return (
                    <div key={idx} className="border border-gray-200 rounded-aub p-4">
                      <div className="flex items-start gap-3 mb-2">
                        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-bold">
                          {err.segment_index}
                        </div>
                        <div className="flex-1">
                          <div className="text-sm text-gray-800 font-mono bg-red-50 p-2 rounded mb-2">
                            {err.segment_text}
                          </div>
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${typeDisplay.color}`}>
                            {typeDisplay.label}
                          </span>
                          {err.error_type === 'custom' && err.custom_description && (
                            <div className="mt-2 text-sm text-gray-700">
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

            {submission.workflow_suggestion && (
              <div>
                <h3 className="font-medium text-gray-700 mb-2">Workflow Suggestion</h3>
                <div className="bg-blue-50 p-3 rounded-aub text-gray-700">
                  {submission.workflow_suggestion}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Reference Solution */}
        {referenceSolution && (
          <div className="card">
            <h2 className="text-xl font-semibold text-aub-black mb-4">
              🎯 Reference Solution
            </h2>
            <div className="bg-green-50 p-4 rounded-aub">
              <MarkdownRenderer content={referenceSolution} />
            </div>
          </div>
        )}
      </div>
    );
  }

  // Challenge view (no submission yet)
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <button onClick={() => router.back()} className="text-aub-red hover:text-aub-black mb-4">
          ← Back to Challenges
        </button>
        <h1 className="text-3xl font-bold text-aub-black">{challenge.title}</h1>
        <div className="flex items-center gap-3 mt-2">
          <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyColor(challenge.difficulty)}`}>
            {challenge.difficulty}
          </span>
          {challenge.tags.map((tag, i) => (
            <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">📋 Instructions</h3>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>Read the AI&apos;s solution below carefully</li>
          <li>Click on ALL steps you think are incorrect</li>
          <li>For each selected error, classify the type of mistake</li>
          <li>Optionally suggest a better workflow approach</li>
          <li>Submit to unlock the reference solution!</li>
        </ol>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-aub p-4 text-red-800">
          {error}
        </div>
      )}

      {/* Problem Statement */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">Problem Statement</h2>
        <MarkdownRenderer content={challenge.problem_statement} />
      </div>

      {/* AI Solution with Selection */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          AI&apos;s Solution - Select All Incorrect Steps
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Click on a step to mark it as incorrect. You can select multiple steps.
        </p>

        <div className="space-y-3">
          {aiSolutionSegments.map((segment, index) => {
            const isSelected = isSegmentSelected(index);
            const selectedError = getSelectedError(index);

            return (
              <div key={index} className="border-2 rounded-aub transition-all">
                {/* Segment Selection */}
                <div
                  onClick={() => handleToggleSegment(index, segment)}
                  className={`p-4 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-red-500 bg-red-50'
                      : 'border-gray-200 bg-white hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      isSelected
                        ? 'bg-red-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {index}
                    </div>
                    <div className="flex-1 text-sm text-gray-800 font-mono">
                      {segment}
                    </div>
                    {isSelected && (
                      <div className="flex-shrink-0 text-red-500 text-xl">✓</div>
                    )}
                  </div>
                </div>

                {/* Error Classification (shown when selected) */}
                {isSelected && selectedError && (
                  <div className="px-4 pb-4 bg-red-50 border-t-2 border-red-200">
                    <div className="pt-3 space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Error Type *
                        </label>
                        <select
                          value={selectedError.error_type}
                          onChange={(e) => handleUpdateErrorType(index, e.target.value)}
                          className="input-primary w-full"
                        >
                          {errorTypeOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      {selectedError.error_type === 'custom' && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Describe the error *
                          </label>
                          <input
                            type="text"
                            value={selectedError.custom_description || ''}
                            onChange={(e) => handleUpdateCustomDescription(index, e.target.value)}
                            className="input-primary w-full"
                            placeholder="Explain what's wrong with this step..."
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {selectedErrors.length > 0 && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-aub">
          <p className="text-green-800 text-sm">
            ✓ You&apos;ve selected {selectedErrors.length} error{selectedErrors.length > 1 ? 's' : ''}.
          </p>
          </div>
        )}
      </div>

      {/* Workflow Suggestion (Optional) */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Better Workflow Suggestion (Optional)
        </h2>
        <p className="text-sm text-gray-600 mb-3">
          If you have suggestions for a better approach or workflow, share them here.
        </p>
        <textarea
          value={workflowSuggestion}
          onChange={(e) => setWorkflowSuggestion(e.target.value)}
          rows={4}
          className="input-primary w-full"
          placeholder="Optional: Suggest a better way to approach this problem..."
        />
      </div>

      {/* Submit Button */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {selectedErrors.length === 0 ? (
            'Select at least one incorrect step to submit'
          ) : !canSubmit ? (
            'Please provide descriptions for all custom error types'
          ) : (
            `Ready to submit with ${selectedErrors.length} error${selectedErrors.length > 1 ? 's' : ''} identified`
          )}
        </div>

        <button
          onClick={handleSubmit}
          className="btn-primary"
          disabled={!canSubmit || submitting}
        >
          {submitting ? (
            <>
              <span className="spinner mr-2"></span>
              Submitting...
            </>
          ) : (
            '🎯 Submit & Unlock Solution'
          )}
        </button>
      </div>
    </div>
  );
}
