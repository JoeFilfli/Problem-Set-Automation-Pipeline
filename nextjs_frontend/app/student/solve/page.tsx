'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

/**
 * Guided Problem Solving Page
 * Interactive step-by-step problem solving with AI guidance
 */

type MCQOption = {
  A: string;
  B: string;
  C: string;
  D: string;
};

type Step = {
  step_number: number;
  title: string;
  explanation: string;
  mcq: {
    question: string;
    options: MCQOption;
  };
  points: number;
};

type Problem = {
  id?: number;
  statement: string;
  topic?: string;
  difficulty?: string;
  given?: string[];
  required?: string[];
};

type SessionSummary = {
  total_score: number;
  max_score: number;
  percentage: number;
  steps_completed: number;
  performance: string;
  final_answer: string;
  step_results: Array<{
    step: number;
    attempts: number;
    hints_used: number;
    score: number;
    gave_up?: boolean;
  }>;
};

type ProblemSet = {
  id: string;
  title: string;
  doc_id: string;
  problem_set: Array<{
    problem: Problem;
    solution: string;
  }>;
};

// Main component that uses useSearchParams
function GuidedSolvePageContent() {
  const searchParams = useSearchParams();
  const preselectedProblemSetId = searchParams.get('problemSetId');
  // Problem selection state
  const [problemSets, setProblemSets] = useState<ProblemSet[]>([]);
  const [selectedProblemSet, setSelectedProblemSet] = useState<ProblemSet | null>(null);
  const [selectedProblemIndex, setSelectedProblemIndex] = useState<number>(0);
  const [difficulty, setDifficulty] = useState<string>('medium');
  const [isLoadingProblemSets, setIsLoadingProblemSets] = useState(true);

  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<Step | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [score, setScore] = useState(0);
  const [maxScore, setMaxScore] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  const [summary, setSummary] = useState<SessionSummary | null>(null);

  // Interaction state
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackType, setFeedbackType] = useState<'success' | 'error' | 'info'>('info');
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [currentHint, setCurrentHint] = useState<string | null>(null);
  const [isLoadingHint, setIsLoadingHint] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Message history for chat-like display
  const [messages, setMessages] = useState<Array<{
    type: 'system' | 'user' | 'ai';
    content: string;
    isCorrect?: boolean;
  }>>([]);

  // Load problem sets on mount and handle preselection from URL
  useEffect(() => {
    fetchProblemSets();
  }, []);

  // Auto-select problem set from URL parameter
  useEffect(() => {
    if (preselectedProblemSetId && problemSets.length > 0) {
      const preselected = problemSets.find(ps => ps.id === preselectedProblemSetId);
      if (preselected) {
        setSelectedProblemSet(preselected);
        setSelectedProblemIndex(0);
      }
    }
  }, [preselectedProblemSetId, problemSets]);

  const fetchProblemSets = async () => {
    try {
      setIsLoadingProblemSets(true);
      const res = await fetch('http://127.0.0.1:8000/api/py/problem-sets');
      if (!res.ok) throw new Error('Failed to load problem sets');
      const data = await res.json();
      
      // Fetch full details for each problem set
      const fullSets: ProblemSet[] = [];
      for (const ps of data.problem_sets || []) {
        try {
          const detailRes = await fetch(`http://127.0.0.1:8000/api/py/problem-sets/${ps.id}`);
          if (detailRes.ok) {
            const detail = await detailRes.json();
            fullSets.push(detail.problem_set);
          }
        } catch (e) {
          console.error('Error loading problem set details:', e);
        }
      }
      
      setProblemSets(fullSets);
    } catch (err: any) {
      console.error('Error loading problem sets:', err);
      setError('Could not load problem sets. Make sure the backend is running.');
    } finally {
      setIsLoadingProblemSets(false);
    }
  };

  const startSession = async () => {
    if (!selectedProblemSet) return;
    
    const problem = selectedProblemSet.problem_set[selectedProblemIndex]?.problem;
    if (!problem) return;

    try {
      setIsStarting(true);
      setError(null);
      setMessages([]);
      setFeedback(null);
      setShowExplanation(false);
      setExplanation(null);
      setCurrentHint(null);
      setHintsUsed(0);
      setAttempts(0);

      console.log('Starting session with problem:', problem);
      
      const res = await fetch('http://127.0.0.1:8000/api/py/guided/start-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem, difficulty })
      });

      if (!res.ok) {
        let errMessage = `HTTP ${res.status}`;
        try {
          const errData = await res.json();
          errMessage = errData.detail || errData.error || errData.message || JSON.stringify(errData);
        } catch {
          // If JSON parsing fails, try text
          try {
            errMessage = await res.text();
          } catch {
            // ignore
          }
        }
        throw new Error(errMessage);
      }

      const data = await res.json();
      
      setSessionId(data.session_id);
      setCurrentStep(data.step);
      setStepIndex(data.current_step);
      setTotalSteps(data.total_steps);
      setScore(data.score);
      setMaxScore(data.max_score);
      setIsCompleted(false);
      setSummary(null);
      setSelectedAnswer(null);

      // Add welcome message
      setMessages([
        {
          type: 'ai',
          content: `🎯 Let's solve this problem together! I'll guide you through ${data.total_steps} steps. Each step has a question to check your understanding. You can earn up to ${data.max_score} points!`
        },
        {
          type: 'system',
          content: `Step 1 of ${data.total_steps}: ${data.step.title}`
        }
      ]);

    } catch (err: any) {
      console.error('Error starting session:', err);
      setError(err.message || 'Failed to start guided solving session');
    } finally {
      setIsStarting(false);
    }
  };

  const submitAnswer = async () => {
    if (!sessionId || !selectedAnswer || !currentStep) return;

    try {
      setIsSubmitting(true);
      setFeedback(null);
      setShowExplanation(false);

      const res = await fetch('http://127.0.0.1:8000/api/py/guided/submit-answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          step_index: stepIndex,
          answer: selectedAnswer
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to submit answer');
      }

      const data = await res.json();
      
      // Add user's answer to messages
      const optionText = currentStep.mcq.options[selectedAnswer as keyof MCQOption];
      setMessages(prev => [...prev, {
        type: 'user',
        content: `${selectedAnswer}: ${optionText}`,
        isCorrect: data.is_correct
      }]);

      setAttempts(data.attempts);
      setFeedback(data.feedback);
      setFeedbackType(data.is_correct ? 'success' : 'error');

      // Add AI feedback
      setMessages(prev => [...prev, {
        type: 'ai',
        content: data.feedback
      }]);

      // If wrong, show explanation for why their answer was wrong
      if (!data.is_correct && data.wrong_explanation) {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: `❌ **Why "${selectedAnswer}" is incorrect:** ${data.wrong_explanation}`
        }]);
      }

      if (data.is_correct || data.correct_answer) {
        // Show explanation
        setShowExplanation(true);
        setExplanation(data.explanation);
        
        if (data.score_earned !== undefined) {
          setMessages(prev => [...prev, {
            type: 'system',
            content: `+${data.score_earned} points! 🎉`
          }]);
        }

        setScore(data.total_score || score);

        if (data.completed) {
          // Session complete
          setIsCompleted(true);
          setSummary(data.summary);
          setCurrentStep(null);
          
          setMessages(prev => [...prev, {
            type: 'ai',
            content: `🏆 Congratulations! You've completed the problem! ${data.summary.performance}`
          }]);
        } else if (data.next_step) {
          // Move to next step after a delay
          setTimeout(() => {
            setCurrentStep(data.next_step);
            setStepIndex(data.current_step);
            setSelectedAnswer(null);
            setFeedback(null);
            setShowExplanation(false);
            setExplanation(null);
            setCurrentHint(null);
            setHintsUsed(0);
            setAttempts(0);

            setMessages(prev => [...prev, {
              type: 'system',
              content: `Step ${data.current_step + 1} of ${totalSteps}: ${data.next_step.title}`
            }]);
          }, 2000);
        }
      }

      setSelectedAnswer(null);

    } catch (err: any) {
      console.error('Error submitting answer:', err);
      setError(err.message || 'Failed to submit answer');
    } finally {
      setIsSubmitting(false);
    }
  };

  const requestHint = async () => {
    if (!sessionId) return;

    try {
      setIsLoadingHint(true);

      const res = await fetch('http://127.0.0.1:8000/api/py/guided/get-hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          step_index: stepIndex,
          hints_used: hintsUsed
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to get hint');
      }

      const data = await res.json();

      if (data.hint) {
        setCurrentHint(data.hint);
        setHintsUsed(data.hint_number);
        
        setMessages(prev => [...prev, {
          type: 'ai',
          content: `💡 Hint ${data.hint_number}: ${data.hint}`
        }]);
      } else {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: '🤷 No more hints available for this step!'
        }]);
      }

    } catch (err: any) {
      console.error('Error getting hint:', err);
    } finally {
      setIsLoadingHint(false);
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setCurrentStep(null);
    setStepIndex(0);
    setTotalSteps(0);
    setScore(0);
    setMaxScore(0);
    setIsCompleted(false);
    setSummary(null);
    setSelectedAnswer(null);
    setFeedback(null);
    setShowExplanation(false);
    setExplanation(null);
    setCurrentHint(null);
    setHintsUsed(0);
    setAttempts(0);
    setMessages([]);
    setError(null);
  };

  // Problem selection view
  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-aub-cream to-white">
        <div className="container-aub py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <Link href="/student" className="text-aub-red hover:underline text-sm mb-2 inline-block">
                ← Back to Student Portal
              </Link>
              <h1 className="text-3xl font-bold text-aub-black">🎮 Guided Problem Solving</h1>
              <p className="text-gray-600 mt-2">
                Learn step-by-step with AI guidance. Answer questions, get hints, and master the material!
              </p>
            </div>
          </div>

          {error && (
            <div className="alert-error mb-6">
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          )}

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Problem Selection Card */}
            <div className="card">
              <h2 className="text-xl font-bold mb-4">Select a Problem</h2>
              
              {isLoadingProblemSets ? (
                <div className="flex items-center justify-center py-12">
                  <div className="spinner-lg"></div>
                  <span className="ml-3 text-gray-600">Loading problem sets...</span>
                </div>
              ) : problemSets.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-4xl mb-4">📚</p>
                  <p>No problem sets available yet.</p>
                  <p className="text-sm mt-2">Generate some problems from the Professor Portal first!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Problem Set Selector */}
                  <div>
                    <label className="label">Problem Set</label>
                    <select
                      className="select"
                      value={selectedProblemSet?.id || ''}
                      onChange={(e) => {
                        const ps = problemSets.find(p => p.id === e.target.value);
                        setSelectedProblemSet(ps || null);
                        setSelectedProblemIndex(0);
                      }}
                    >
                      <option value="">Choose a problem set...</option>
                      {problemSets.map((ps) => (
                        <option key={ps.id} value={ps.id}>
                          {ps.title || ps.doc_id}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Problem Selector */}
                  {selectedProblemSet && (
                    <div>
                      <label className="label">Problem</label>
                      <select
                        className="select"
                        value={selectedProblemIndex}
                        onChange={(e) => setSelectedProblemIndex(Number(e.target.value))}
                      >
                        {selectedProblemSet.problem_set.map((item, idx) => (
                          <option key={idx} value={idx}>
                            Problem {idx + 1}: {item.problem.topic || 'General'} ({item.problem.difficulty || 'medium'})
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Difficulty Selector */}
                  <div>
                    <label className="label">Guidance Level</label>
                    <div className="flex gap-2">
                      {['easy', 'medium', 'hard'].map((d) => (
                        <button
                          key={d}
                          onClick={() => setDifficulty(d)}
                          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                            difficulty === d
                              ? 'bg-aub-red text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {d === 'easy' ? '🌱 Easy' : d === 'medium' ? '🌿 Medium' : '🌳 Hard'}
                          <span className="block text-xs opacity-75">
                            {d === 'easy' ? '3 steps' : d === 'medium' ? '5 steps' : '7 steps'}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Problem Preview Card */}
            <div className="card">
              <h2 className="text-xl font-bold mb-4">Problem Preview</h2>
              
              {selectedProblemSet && selectedProblemSet.problem_set[selectedProblemIndex] ? (
                <div className="space-y-4">
                  <div className="flex gap-2">
                    {selectedProblemSet.problem_set[selectedProblemIndex].problem.topic && (
                      <span className="badge-red">
                        {selectedProblemSet.problem_set[selectedProblemIndex].problem.topic}
                      </span>
                    )}
                    {selectedProblemSet.problem_set[selectedProblemIndex].problem.difficulty && (
                      <span className="badge-gray">
                        {selectedProblemSet.problem_set[selectedProblemIndex].problem.difficulty}
                      </span>
                    )}
                  </div>

                  <div className="bg-aub-beige p-4 rounded-lg">
                    <p className="text-gray-800 whitespace-pre-wrap">
                      {selectedProblemSet.problem_set[selectedProblemIndex].problem.statement}
                    </p>
                  </div>

                  {selectedProblemSet.problem_set[selectedProblemIndex].problem.given && (
                    <div>
                      <h4 className="font-medium text-gray-700 mb-2">Given:</h4>
                      <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
                        {selectedProblemSet.problem_set[selectedProblemIndex].problem.given.map((g, i) => (
                          <li key={i}>{g}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedProblemSet.problem_set[selectedProblemIndex].problem.required && (
                    <div>
                      <h4 className="font-medium text-gray-700 mb-2">Find:</h4>
                      <ul className="list-disc list-inside text-gray-600 text-sm space-y-1">
                        {selectedProblemSet.problem_set[selectedProblemIndex].problem.required.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <button
                    onClick={startSession}
                    disabled={isStarting}
                    className="btn-primary w-full py-3 text-lg"
                  >
                    {isStarting ? (
                      <>
                        <span className="spinner mr-2"></span>
                        Preparing your guided session... (this may take 10-20 seconds)
                      </>
                    ) : (
                      '🚀 Start Guided Solving'
                    )}
                  </button>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-4xl mb-4">👈</p>
                  <p>Select a problem set and problem to preview</p>
                </div>
              )}
            </div>
          </div>

          {/* How it works */}
          <div className="mt-12 card">
            <h2 className="text-xl font-bold mb-4">How It Works</h2>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-4xl mb-2">📖</div>
                <h3 className="font-medium">1. Read the Step</h3>
                <p className="text-sm text-gray-600">Each step explains a concept or approach</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-2">❓</div>
                <h3 className="font-medium">2. Answer the MCQ</h3>
                <p className="text-sm text-gray-600">Test your understanding with a question</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-2">💡</div>
                <h3 className="font-medium">3. Use Hints</h3>
                <p className="text-sm text-gray-600">Get help if you&apos;re stuck (costs points)</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-2">🏆</div>
                <h3 className="font-medium">4. Earn Points</h3>
                <p className="text-sm text-gray-600">Score based on attempts and hints used</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Active session view
  return (
    <div className="min-h-screen bg-gradient-to-br from-aub-cream to-white">
      <div className="container-aub py-6">
        {/* Header with progress */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <button
              onClick={resetSession}
              className="text-aub-red hover:underline text-sm mb-1"
            >
              ← Exit Session
            </button>
            <h1 className="text-2xl font-bold text-aub-black">Guided Problem Solving</h1>
          </div>
          
          <div className="flex items-center gap-6">
            {/* Score */}
            <div className="text-center">
              <div className="text-2xl font-bold text-aub-red">{score}</div>
              <div className="text-xs text-gray-500">/ {maxScore} pts</div>
            </div>
            
            {/* Progress */}
            <div className="w-48">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Step {stepIndex + 1} of {totalSteps}</span>
                <span>{Math.round(((stepIndex + (isCompleted ? 1 : 0)) / totalSteps) * 100)}%</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${((stepIndex + (isCompleted ? 1 : 0)) / totalSteps) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Chat/Message Area - Now larger */}
          <div className="lg:col-span-3">
            <div className="card min-h-[700px] flex flex-col">
              {/* Messages - Larger scrollable area */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 custom-scrollbar p-4 max-h-[400px]">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`${
                      msg.type === 'user'
                        ? 'chat-message-user text-base'
                        : msg.type === 'ai'
                        ? 'chat-message-assistant text-base leading-relaxed'
                        : 'text-center text-sm text-gray-500 py-3 border-y border-gray-200 bg-gray-50 font-medium'
                    } ${msg.isCorrect === true ? 'ring-2 ring-green-400' : msg.isCorrect === false ? 'ring-2 ring-red-400' : ''}`}
                  >
                    {msg.content}
                  </div>
                ))}
              </div>

              {/* Current Step MCQ */}
              {currentStep && !isCompleted && (
                <div className="border-t pt-6 px-2">
                  {/* Step explanation - more prominent */}
                  <div className="bg-gradient-to-r from-aub-beige to-white p-5 rounded-xl mb-5 border border-gray-200">
                    <p className="text-gray-600 mb-3 leading-relaxed">{currentStep.explanation}</p>
                    <p className="font-semibold text-gray-900 text-lg">{currentStep.mcq.question}</p>
                  </div>

                  {/* MCQ Options - Bigger and clearer */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">
                    {Object.entries(currentStep.mcq.options).map(([key, value]) => (
                      <button
                        key={key}
                        onClick={() => setSelectedAnswer(key)}
                        disabled={isSubmitting}
                        className={`p-4 rounded-xl text-left transition-all border-2 ${
                          selectedAnswer === key
                            ? 'border-aub-red bg-aub-red-pale shadow-md'
                            : 'border-gray-200 hover:border-aub-red/50 hover:bg-gray-50 bg-white'
                        }`}
                      >
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-aub-red text-white font-bold mr-3">{key}</span>
                        <span className="text-gray-700">{value}</span>
                      </button>
                    ))}
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <button
                      onClick={submitAnswer}
                      disabled={!selectedAnswer || isSubmitting}
                      className="btn-primary flex-1"
                    >
                      {isSubmitting ? (
                        <>
                          <span className="spinner mr-2"></span>
                          Checking...
                        </>
                      ) : (
                        'Submit Answer'
                      )}
                    </button>
                    <button
                      onClick={requestHint}
                      disabled={isLoadingHint || hintsUsed >= 2}
                      className="btn-secondary"
                      title={hintsUsed >= 2 ? 'No more hints available' : 'Get a hint (-3 pts)'}
                    >
                      {isLoadingHint ? (
                        <span className="spinner"></span>
                      ) : (
                        <>💡 Hint ({2 - hintsUsed} left)</>
                      )}
                    </button>
                  </div>

                  {/* Current hint display */}
                  {currentHint && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm text-yellow-800">
                        <span className="font-medium">💡 Hint:</span> {currentHint}
                      </p>
                    </div>
                  )}

                  {/* Explanation after correct answer */}
                  {showExplanation && explanation && (
                    <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-800">
                        <span className="font-medium">✅ Explanation:</span> {explanation}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Completion Summary */}
              {isCompleted && summary && (
                <div className="border-t pt-4">
                  <div className="bg-gradient-to-r from-aub-red to-aub-red-light p-6 rounded-lg text-white text-center">
                    <div className="text-5xl mb-3">🎉</div>
                    <h2 className="text-2xl font-bold mb-2">Problem Complete!</h2>
                    <p className="text-lg opacity-90">{summary.performance}</p>
                    
                    <div className="grid grid-cols-3 gap-4 mt-6">
                      <div className="bg-white/20 rounded-lg p-3">
                        <div className="text-3xl font-bold">{summary.total_score}</div>
                        <div className="text-sm opacity-75">Points Earned</div>
                      </div>
                      <div className="bg-white/20 rounded-lg p-3">
                        <div className="text-3xl font-bold">{summary.percentage}%</div>
                        <div className="text-sm opacity-75">Accuracy</div>
                      </div>
                      <div className="bg-white/20 rounded-lg p-3">
                        <div className="text-3xl font-bold">{summary.steps_completed}</div>
                        <div className="text-sm opacity-75">Steps Done</div>
                      </div>
                    </div>

                    <button
                      onClick={resetSession}
                      className="mt-6 bg-white text-aub-red px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
                    >
                      Try Another Problem
                    </button>
                  </div>

                  {/* Final Answer */}
                  {summary.final_answer && (
                    <div className="mt-4 p-4 bg-aub-beige rounded-lg">
                      <h3 className="font-bold text-gray-800 mb-2">📝 Complete Solution</h3>
                      <p className="text-gray-700 whitespace-pre-wrap">{summary.final_answer}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - Problem & Stats - Compact */}
          <div className="space-y-3">
            {/* Problem Card - Collapsible */}
            <details className="card" open>
              <summary className="font-bold text-gray-800 cursor-pointer hover:text-aub-red">📋 Problem</summary>
              {selectedProblemSet && selectedProblemSet.problem_set[selectedProblemIndex] && (
                <div className="text-sm text-gray-600 space-y-2 mt-3">
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {selectedProblemSet.problem_set[selectedProblemIndex].problem.statement}
                  </p>
                  {selectedProblemSet.problem_set[selectedProblemIndex].problem.given && (
                    <div className="mt-2 pt-2 border-t">
                      <span className="font-medium">Given:</span>
                      <ul className="list-disc list-inside mt-1 text-xs">
                        {selectedProblemSet.problem_set[selectedProblemIndex].problem.given.map((g, i) => (
                          <li key={i}>{g}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </details>

            {/* Stats Card - Always visible */}
            <div className="card bg-gradient-to-br from-white to-aub-beige">
              <h3 className="font-bold text-gray-800 mb-3 text-sm">📊 Step Stats</h3>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-white rounded-lg p-2 shadow-sm">
                  <div className="text-lg font-bold text-aub-red">{attempts}</div>
                  <div className="text-xs text-gray-500">Tries</div>
                </div>
                <div className="bg-white rounded-lg p-2 shadow-sm">
                  <div className="text-lg font-bold text-yellow-600">{hintsUsed}/2</div>
                  <div className="text-xs text-gray-500">Hints</div>
                </div>
                <div className="bg-white rounded-lg p-2 shadow-sm">
                  <div className="text-lg font-bold text-green-600">{currentStep?.points || 0}</div>
                  <div className="text-xs text-gray-500">Points</div>
                </div>
              </div>
            </div>

            {/* Tips Card - Compact */}
            <div className="card bg-blue-50 border border-blue-200 text-xs">
              <h3 className="font-bold text-blue-800 mb-2 text-sm">💡 Scoring</h3>
              <ul className="text-blue-700 space-y-0.5">
                <li>• 1st try = full points</li>
                <li>• Extra try = -2 pts</li>
                <li>• Hint = -3 pts</li>
                <li>• 3 wrong = revealed</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Wrapper component with Suspense boundary
// This is required by Next.js for components using useSearchParams()
export default function GuidedSolvePage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading problem solving interface...</p>
        </div>
      </div>
    }>
      <GuidedSolvePageContent />
    </Suspense>
  );
}
