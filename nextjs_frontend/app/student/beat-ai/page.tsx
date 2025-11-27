'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getAvailableChallenges } from '@/lib/api/beatAi';
import type { BeatAIChallengeStudent } from '@/lib/types';

/**
 * Beat the AI Challenges List (Student View)
 * Display available challenges for students to attempt
 */
export default function StudentBeatAIPage() {
  // State for challenges list
  const [challenges, setChallenges] = useState<BeatAIChallengeStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'EASY' | 'MEDIUM' | 'HARD'>('ALL');

  // Load challenges from backend
  useEffect(() => {
    loadChallenges();
  }, []);

  const loadChallenges = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAvailableChallenges();
      setChallenges(data);
    } catch (err: any) {
      console.error('Error loading challenges:', err);
      setError(err.message || 'Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  // Filter challenges by difficulty
  const filteredChallenges = filter === 'ALL'
    ? challenges
    : challenges.filter(c => c.difficulty === filter);

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
          <p className="text-gray-600">Loading challenges...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Beat the AI Challenges</h1>
        <p className="text-gray-600 mt-2">
          Find the error in AI solutions and prove you&apos;re smarter than the machine! 🤖💪
        </p>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-aub p-4 text-red-800">
          {error}
        </div>
      )}

      {/* Filter Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('ALL')}
          className={`px-4 py-2 rounded-aub font-medium transition-colors ${
            filter === 'ALL'
              ? 'bg-aub-red text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All ({challenges.length})
        </button>
        <button
          onClick={() => setFilter('EASY')}
          className={`px-4 py-2 rounded-aub font-medium transition-colors ${
            filter === 'EASY'
              ? 'bg-green-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Easy ({challenges.filter(c => c.difficulty === 'EASY').length})
        </button>
        <button
          onClick={() => setFilter('MEDIUM')}
          className={`px-4 py-2 rounded-aub font-medium transition-colors ${
            filter === 'MEDIUM'
              ? 'bg-yellow-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Medium ({challenges.filter(c => c.difficulty === 'MEDIUM').length})
        </button>
        <button
          onClick={() => setFilter('HARD')}
          className={`px-4 py-2 rounded-aub font-medium transition-colors ${
            filter === 'HARD'
              ? 'bg-red-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Hard ({challenges.filter(c => c.difficulty === 'HARD').length})
        </button>
      </div>

      {/* Challenges Grid */}
      {filteredChallenges.length === 0 ? (
        <div className="card text-center py-12 text-gray-500">
          <p className="text-lg">No challenges available{filter !== 'ALL' ? ` for ${filter} difficulty` : ''}.</p>
          {filter !== 'ALL' && (
            <button
              onClick={() => setFilter('ALL')}
              className="text-aub-red hover:text-aub-black mt-2 inline-block"
            >
              View all challenges →
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredChallenges.map((challenge) => (
            <div
              key={challenge.id}
              className="card hover:shadow-xl transition-shadow"
            >
              {/* Challenge Header */}
              <div className="mb-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    {challenge.title}
                  </h3>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getDifficultyColor(challenge.difficulty)}`}>
                    {challenge.difficulty}
                  </span>
                </div>

                {/* Tags */}
                {challenge.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {challenge.tags.slice(0, 3).map((tag, i) => (
                      <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                        {tag}
                      </span>
                    ))}
                    {challenge.tags.length > 3 && (
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                        +{challenge.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Problem Preview */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 line-clamp-3">
                  {challenge.problem_statement}
                </p>
              </div>

              {/* AI Solution Status */}
              {challenge.ai_wrong_solution ? (
                <div className="flex items-center gap-2 mb-4 text-sm">
                  <span className="text-green-600">✓</span>
                  <span className="text-gray-600">AI solution available</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 mb-4 text-sm">
                  <span className="text-red-600">✗</span>
                  <span className="text-gray-600">AI solution not ready</span>
                </div>
              )}

              {/* Action Button */}
              <Link
                href={`/student/beat-ai/${challenge.id}`}
                className={`btn-primary w-full text-center ${
                  !challenge.ai_wrong_solution ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                onClick={(e) => {
                  if (!challenge.ai_wrong_solution) {
                    e.preventDefault();
                    alert('This challenge is not ready yet. The AI solution needs to be generated first.');
                  }
                }}
              >
                Beat the AI →
              </Link>
            </div>
          ))}
        </div>
      )}

      {/* Info Box */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">🎯 How to Beat the AI</h3>
        <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
          <li>Read the problem and the AI&apos;s solution carefully</li>
          <li>Find the error in the AI&apos;s reasoning (it&apos;s subtle!)</li>
          <li>Explain why the AI is wrong and provide the correct approach</li>
          <li>Reflect on what you learned from finding the error</li>
          <li>Submit and unlock the reference solution!</li>
        </ol>
      </div>
    </div>
  );
}

