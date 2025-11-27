'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getMyChallenges, deleteChallenge } from '@/lib/api/beatAi';
import type { BeatAIChallenge } from '@/lib/types';

/**
 * Beat the AI Challenges Page (Professor View)
 * List and manage "Beat the AI" challenges
 */
export default function BeatAIChallengesPage() {
  // State for challenges list
  const [challenges, setChallenges] = useState<BeatAIChallenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load challenges from backend
  useEffect(() => {
    loadChallenges();
  }, []);

  const loadChallenges = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getMyChallenges();
      setChallenges(data);
    } catch (err: any) {
      console.error('Error loading challenges:', err);
      setError(err.message || 'Failed to load challenges');
    } finally {
      setLoading(false);
    }
  };

  // Delete challenge handler
  const handleDelete = async (challengeId: string) => {
    if (!confirm('Are you sure you want to delete this challenge? This will also delete all submissions.')) {
      return;
    }

    try {
      await deleteChallenge(challengeId);
      // Remove from state
      setChallenges(prev => prev.filter(c => c.id !== challengeId));
    } catch (err: any) {
      console.error('Error deleting challenge:', err);
      alert('Failed to delete challenge: ' + err.message);
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
          Create challenges where students debug wrong AI solutions
        </p>
      </div>

      {/* Create Challenge Button */}
      <div>
        <Link href="/professor/beat-ai/new" className="btn-primary">
          ✨ Create Challenge
        </Link>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-aub p-4 text-red-800">
          {error}
        </div>
      )}

      {/* Challenges Table */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Your Challenges ({challenges.length})
        </h2>

        {challenges.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No challenges created yet.</p>
            <Link 
              href="/professor/beat-ai/new" 
              className="text-aub-red hover:text-aub-black mt-2 inline-block"
            >
              Create your first challenge →
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Difficulty
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submissions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {challenges.map((challenge) => (
                  <tr key={challenge.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {challenge.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getDifficultyColor(challenge.difficulty)}`}>
                        {challenge.difficulty}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {challenge.tags.slice(0, 2).map((tag, i) => (
                          <span key={i} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                            {tag}
                          </span>
                        ))}
                        {challenge.tags.length > 2 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                            +{challenge.tags.length - 2}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {challenge.submission_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {challenge.avg_score ? `${challenge.avg_score.toFixed(1)}%` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(challenge.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link
                        href={`/professor/beat-ai/${challenge.id}`}
                        className="text-aub-red hover:text-aub-black mr-4"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(challenge.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      {challenges.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="text-sm text-gray-600">Total Challenges</div>
            <div className="text-2xl font-bold text-aub-black mt-1">
              {challenges.length}
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Total Submissions</div>
            <div className="text-2xl font-bold text-aub-black mt-1">
              {challenges.reduce((sum, c) => sum + (c.submission_count || 0), 0)}
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">Avg Score</div>
            <div className="text-2xl font-bold text-aub-black mt-1">
              {challenges.length > 0
                ? (challenges.reduce((sum, c) => sum + (c.avg_score || 0), 0) / challenges.length).toFixed(1)
                : 0}%
            </div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-600">With AI Solution</div>
            <div className="text-2xl font-bold text-aub-black mt-1">
              {challenges.filter(c => c.ai_wrong_solution).length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

