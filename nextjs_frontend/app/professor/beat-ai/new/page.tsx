'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  generateChallengeFromChapter,
  getAvailableChapters,
} from '@/lib/api/beatAi';
import type { GenerateProblemFromChapterRequest } from '@/lib/types';

/**
 * Create Beat the AI Challenge Page (Professor)
 * One-click generation: Select chapter and auto-create challenge
 */
export default function CreateChallengePage() {
  const router = useRouter();

  // Available chapters
  const [chapters, setChapters] = useState<string[]>([]);
  const [loadingChapters, setLoadingChapters] = useState(true);

  // Form inputs
  const [chapterId, setChapterId] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState<'EASY' | 'MEDIUM' | 'HARD'>('MEDIUM');

  // UI state
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load available chapters
  useEffect(() => {
    loadChapters();
  }, []);

  const loadChapters = async () => {
    try {
      setLoadingChapters(true);
      const availableChapters = await getAvailableChapters();
      setChapters(availableChapters);
    } catch (err: any) {
      console.error('Error loading chapters:', err);
      setError('Failed to load chapters: ' + err.message);
    } finally {
      setLoadingChapters(false);
    }
  };

  // Handle automatic challenge generation
  const handleGenerateChallenge = async () => {
    if (!chapterId) {
      setError('Please select a chapter');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setSuccess(false);

      const request: GenerateProblemFromChapterRequest = {
        chapter_id: chapterId,
        topic: topic || undefined,
        difficulty,
      };

      // This generates problem, wrong solution, and creates the challenge all in one go
      const challenge = await generateChallengeFromChapter(request);

      setSuccess(true);
      
      // Redirect to the challenge detail page after short delay
      setTimeout(() => {
        router.push(`/professor/beat-ai/${challenge.id}`);
      }, 1500);
    } catch (err: any) {
      console.error('Error generating challenge:', err);
      setError(err.message || 'Failed to generate challenge');
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Generate Beat the AI Challenge</h1>
        <p className="text-gray-600 mt-2">
          Select a chapter and let AI create a complete challenge automatically!
        </p>
      </div>

      {/* Success message */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-aub p-4">
          <div className="flex items-center gap-2 text-green-800">
            <span className="text-2xl">✓</span>
            <div>
              <p className="font-semibold">Challenge created successfully!</p>
              <p className="text-sm">Redirecting to challenge details...</p>
            </div>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-aub p-4 text-red-800">
          {error}
        </div>
      )}

      {/* Generation Form */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-6">
          Challenge Configuration
        </h2>

        <div className="space-y-6">
          {/* Chapter Selection */}
          <div>
            <label htmlFor="chapter" className="block text-sm font-medium text-gray-700 mb-2">
              Chapter / Document *
            </label>
            {loadingChapters ? (
              <div className="flex items-center gap-2 text-gray-600">
                <div className="spinner"></div>
                <span>Loading chapters...</span>
              </div>
            ) : chapters.length === 0 ? (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-aub p-3">
                <p className="font-semibold mb-1">No chapters available</p>
                <p>Please upload course materials first from the Materials page.</p>
              </div>
            ) : (
              <select
                id="chapter"
                value={chapterId}
                onChange={(e) => setChapterId(e.target.value)}
                className="input-primary w-full"
                disabled={generating || success}
              >
                <option value="">Select a chapter...</option>
                {chapters.map((chapter) => (
                  <option key={chapter} value={chapter}>
                    {chapter}
                  </option>
                ))}
              </select>
            )}
            <p className="text-xs text-gray-500 mt-1">
              The AI will use content from this chapter to generate the problem
            </p>
          </div>

          {/* Topic (Optional) */}
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
              Specific Topic (Optional)
            </label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="input-primary w-full"
              placeholder="e.g., Linear Regression, Sorting Algorithms, etc."
              disabled={generating || success}
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave blank to generate a problem from the entire chapter
            </p>
          </div>

          {/* Difficulty */}
          <div>
            <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty Level *
            </label>
            <div className="grid grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => setDifficulty('EASY')}
                disabled={generating || success}
                className={`px-4 py-3 rounded-aub border-2 transition-all ${
                  difficulty === 'EASY'
                    ? 'border-green-500 bg-green-50 text-green-900 font-semibold'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                } ${generating || success ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="text-2xl mb-1">😊</div>
                <div className="text-sm">Easy</div>
              </button>
              <button
                type="button"
                onClick={() => setDifficulty('MEDIUM')}
                disabled={generating || success}
                className={`px-4 py-3 rounded-aub border-2 transition-all ${
                  difficulty === 'MEDIUM'
                    ? 'border-yellow-500 bg-yellow-50 text-yellow-900 font-semibold'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                } ${generating || success ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="text-2xl mb-1">🤔</div>
                <div className="text-sm">Medium</div>
              </button>
              <button
                type="button"
                onClick={() => setDifficulty('HARD')}
                disabled={generating || success}
                className={`px-4 py-3 rounded-aub border-2 transition-all ${
                  difficulty === 'HARD'
                    ? 'border-red-500 bg-red-50 text-red-900 font-semibold'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                } ${generating || success ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <div className="text-2xl mb-1">😰</div>
                <div className="text-sm">Hard</div>
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              This affects the complexity of the generated problem
            </p>
          </div>

          {/* Generate Button */}
          <div className="pt-4 border-t">
            <button
              onClick={handleGenerateChallenge}
              className="btn-primary w-full text-lg py-4"
              disabled={!chapterId || generating || success || chapters.length === 0}
            >
              {generating ? (
                <>
                  <span className="spinner-lg mr-3"></span>
                  <span>Generating Challenge... (this may take 30-60 seconds)</span>
                </>
              ) : success ? (
                <>
                  <span className="text-2xl mr-2">✓</span>
                  <span>Challenge Created!</span>
                </>
              ) : (
                <>
                  <span className="text-xl mr-2">🤖</span>
                  <span>Generate Complete Challenge from Chapter</span>
                </>
              )}
            </button>
            <p className="text-xs text-gray-500 mt-2 text-center">
              This will automatically generate the problem, reference solution, and AI wrong solution
            </p>
          </div>
        </div>
      </div>

      {/* What happens next */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-3">🎯 What Happens When You Click Generate?</h3>
        <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
          <li><strong>Retrieves relevant content</strong> from the selected chapter using RAG</li>
          <li><strong>Generates a problem statement</strong> and complete reference solution</li>
          <li><strong>Creates a convincing but wrong AI solution</strong> with a subtle error</li>
          <li><strong>Saves the challenge</strong> ready for students to attempt</li>
          <li><strong>Takes you to the challenge page</strong> where you can review and edit if needed</li>
        </ol>
        <p className="text-sm text-blue-800 mt-3">
          ⏱️ <strong>Time:</strong> Usually takes 30-60 seconds to generate everything
        </p>
      </div>

      {/* Tips */}
      <div className="card bg-purple-50 border-purple-200">
        <h3 className="font-semibold text-purple-900 mb-2">💡 Tips for Best Results</h3>
        <ul className="text-sm text-purple-800 space-y-1 list-disc list-inside">
          <li>Choose chapters with rich, technical content for better problems</li>
          <li>Specify a topic if you want to focus on a specific concept</li>
          <li>Start with Medium difficulty and adjust based on results</li>
          <li>You can edit the generated challenge after it&apos;s created</li>
          <li>Students won&apos;t see the reference solution until after they submit</li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <button
          onClick={() => router.back()}
          className="btn-secondary"
          disabled={generating}
        >
          ← Cancel
        </button>
        {success && (
          <button
            onClick={() => router.push('/professor/beat-ai')}
            className="btn-secondary"
          >
            View All Challenges
          </button>
        )}
      </div>
    </div>
  );
}
