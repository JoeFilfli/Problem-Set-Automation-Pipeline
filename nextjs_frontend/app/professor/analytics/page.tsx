'use client';

import { useState, useEffect } from 'react';
import {
  getAnalyticsProblemSets,
  getProblemSetAnalytics,
  type ProblemSetWithSubmissions,
  type AnalyticsResponse
} from '@/lib/api';
import { getFeedbackSummary } from '@/lib/api/feedback';
import type { FeedbackSummary } from '@/lib/types';

/**
 * Analytics Dashboard
 * View student submission insights, mistakes, and performance
 */
export default function AnalyticsPage() {
  const [problemSets, setProblemSets] = useState<ProblemSetWithSubmissions[]>([]);
  const [selectedProblemSetId, setSelectedProblemSetId] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        // Load problem sets
        const data = await getAnalyticsProblemSets();
        setProblemSets(data.problem_sets);

        // Auto-select first problem set if available
        if (data.problem_sets.length > 0) {
          setSelectedProblemSetId(data.problem_sets[0].id);
        }

        // Load feedback summary
        setFeedbackLoading(true);
        try {
          const feedbackData = await getFeedbackSummary();
          setFeedbackSummary(feedbackData);
        } catch (feedbackErr) {
          console.error('Failed to load feedback:', feedbackErr);
          // Don't block page load if feedback fails
        } finally {
          setFeedbackLoading(false);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load problem sets');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    async function loadAnalytics() {
      if (!selectedProblemSetId) return;

      try {
        setAnalyticsLoading(true);
        const data = await getProblemSetAnalytics(selectedProblemSetId);
        setAnalytics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics');
      } finally {
        setAnalyticsLoading(false);
      }
    }
    loadAnalytics();
  }, [selectedProblemSetId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error && problemSets.length === 0) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error loading analytics</h3>
        <p className="mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Insights into student submissions, performance, and common mistakes
        </p>
      </div>

      {/* Problem Set Selector */}
      {problemSets.length > 0 ? (
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Problem Set
          </label>
          <select
            value={selectedProblemSetId || ''}
            onChange={(e) => setSelectedProblemSetId(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-aub-red focus:border-transparent"
          >
            {problemSets.map((ps) => (
              <option key={ps.id} value={ps.id}>
                {ps.topic} ({ps.submission_count} submissions)
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="alert-info">
          <h3 className="font-semibold">No Submissions Yet</h3>
          <p className="mt-1">
            Analytics will appear here once students submit problem sets.
          </p>
        </div>
      )}

      {/* Analytics Display */}
      {analyticsLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="spinner-lg mb-3"></div>
            <p className="text-gray-600">Loading analytics data...</p>
          </div>
        </div>
      ) : analytics && analytics.has_data && analytics.stats ? (
        <>
          {/* Overview Stats */}
          <div className="grid md:grid-cols-4 gap-6">
            <div className="card bg-gradient-to-br from-blue-50 to-blue-100">
              <div className="text-3xl mb-2">📊</div>
              <div className="text-2xl font-bold text-aub-black">
                {analytics.stats.average_score.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Average Score</div>
            </div>

            <div className="card bg-gradient-to-br from-green-50 to-green-100">
              <div className="text-3xl mb-2">📈</div>
              <div className="text-2xl font-bold text-aub-black">
                {analytics.stats.median_score.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Median Score</div>
            </div>

            <div className="card bg-gradient-to-br from-purple-50 to-purple-100">
              <div className="text-3xl mb-2">✅</div>
              <div className="text-2xl font-bold text-aub-black">
                {analytics.stats.graded_submissions}
              </div>
              <div className="text-sm text-gray-600">Graded Submissions</div>
            </div>

            <div className="card bg-gradient-to-br from-orange-50 to-orange-100">
              <div className="text-3xl mb-2">📝</div>
              <div className="text-2xl font-bold text-aub-black">
                {analytics.stats.total_submissions}
              </div>
              <div className="text-sm text-gray-600">Total Submissions</div>
            </div>
          </div>

          {/* Grade Distribution & Common Mistakes */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Grade Distribution */}
            <div className="card">
              <h2 className="text-xl font-semibold text-aub-black mb-4">
                📊 Grade Distribution
              </h2>
              {Object.keys(analytics.stats.grade_distribution).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(analytics.stats.grade_distribution)
                    .sort(([a], [b]) => a.localeCompare(b))
                    .map(([grade, count]) => (
                      <div key={grade} className="flex items-center gap-4">
                        <span className="font-medium text-lg w-12">{grade}</span>
                        <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-aub-red to-red-400 h-full flex items-center justify-end pr-2 text-white text-xs font-medium"
                            style={{
                              width: `${(count / (analytics.stats?.graded_submissions || 1)) * 100}%`,
                              minWidth: count > 0 ? '30px' : '0',
                            }}
                          >
                            {count}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No grade data</p>
              )}
            </div>

            {/* Common Mistakes */}
            <div className="card">
              <h2 className="text-xl font-semibold text-aub-black mb-4">
                ❌ Common Mistakes
              </h2>
              {analytics.stats.common_errors.length > 0 ? (
                <div className="space-y-3">
                  {analytics.stats.common_errors.map((error, i) => (
                    <div key={i} className="border-l-4 border-red-400 pl-3 py-2 bg-red-50 rounded">
                      <div className="flex justify-between items-start">
                        <p className="text-sm text-gray-800 flex-1">{error.error}</p>
                        <span className="ml-2 px-2 py-1 bg-red-200 text-red-800 text-xs font-semibold rounded">
                          {error.count}x
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No common errors detected</p>
              )}
            </div>
          </div>

          {/* Common Strengths */}
          {analytics.stats.common_strengths.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-aub-black mb-4">
                ✨ Common Strengths
              </h2>
              <div className="grid md:grid-cols-2 gap-3">
                {analytics.stats.common_strengths.map((strength, i) => (
                  <div key={i} className="border-l-4 border-green-400 pl-3 py-2 bg-green-50 rounded">
                    <div className="flex justify-between items-start">
                      <p className="text-sm text-gray-800 flex-1">{strength.strength}</p>
                      <span className="ml-2 px-2 py-1 bg-green-200 text-green-800 text-xs font-semibold rounded">
                        {strength.count}x
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Student Performance Table */}
          {analytics.student_performance && analytics.student_performance.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-aub-black mb-4">
                👥 Student Performance
              </h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Student
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Problem
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Grade
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.student_performance.map((perf, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {perf.student_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          Problem {perf.problem_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {perf.score.toFixed(1)}%
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${perf.grade.startsWith('A') ? 'bg-green-100 text-green-800' :
                            perf.grade.startsWith('B') ? 'bg-blue-100 text-blue-800' :
                              perf.grade.startsWith('C') ? 'bg-yellow-100 text-yellow-800' :
                                perf.grade.startsWith('D') ? 'bg-orange-100 text-orange-800' :
                                  'bg-red-100 text-red-800'
                            }`}>
                            {perf.grade}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Curriculum Optimization */}
          {analytics.curriculum_optimization && (
            <>
              <div className="card bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="text-3xl">🎓</div>
                  <h2 className="text-2xl font-bold text-purple-900">Curriculum Optimization</h2>
                </div>
                <p className="text-purple-700 mb-4">
                  AI-powered insights to improve your course content and student outcomes
                </p>
              </div>

              {/* Problem Difficulty Analysis */}
              {analytics.curriculum_optimization.problem_difficulty.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    📊 Problem Difficulty Analysis
                  </h2>
                  <div className="space-y-2">
                    {analytics.curriculum_optimization.problem_difficulty.map((prob, i) => (
                      <div
                        key={i}
                        className={`flex items-center justify-between p-3 rounded-lg border-l-4 ${prob.color === 'red' ? 'border-red-500 bg-red-50' :
                            prob.color === 'orange' ? 'border-orange-500 bg-orange-50' :
                              prob.color === 'green' ? 'border-green-500 bg-green-50' :
                                'border-blue-500 bg-blue-50'
                          }`}
                      >
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{prob.topic}</div>
                          <div className="text-sm text-gray-600">
                            Problem #{prob.problem_id} • {prob.submission_count} submissions
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-gray-900">{prob.avg_score}%</div>
                          <div className={`text-xs font-semibold ${prob.color === 'red' ? 'text-red-700' :
                              prob.color === 'orange' ? 'text-orange-700' :
                                prob.color === 'green' ? 'text-green-700' :
                                  'text-blue-700'
                            }`}>
                            {prob.difficulty}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
                    <strong>Legend:</strong>
                    <span className="ml-2">🔴 Too Hard (&lt;50%)</span>
                    <span className="ml-2">🟠 Challenging (50-70%)</span>
                    <span className="ml-2">🟢 Appropriate (70-85%)</span>
                    <span className="ml-2">🔵 Too Easy (&gt;85%)</span>
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analytics.curriculum_optimization.recommendations.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    💡 Recommendations
                  </h2>
                  <div className="space-y-3">
                    {analytics.curriculum_optimization.recommendations.map((rec, i) => (
                      <div
                        key={i}
                        className={`p-4 rounded-lg border-l-4 ${rec.severity === 'high' ? 'border-red-500 bg-red-50' :
                            rec.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                              'border-blue-500 bg-blue-50'
                          }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="text-2xl">
                            {rec.severity === 'high' ? '⚠️' : rec.severity === 'medium' ? '⚡' : '💡'}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-1">{rec.title}</h3>
                            <p className="text-sm text-gray-700 mb-2">{rec.description}</p>
                            {rec.problems && rec.problems.length > 0 && (
                              <div className="text-xs text-gray-600">
                                <strong>Affected:</strong> {rec.problems.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Learning Gaps */}
              {analytics.curriculum_optimization.learning_gaps.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    🔍 Identified Learning Gaps
                  </h2>
                  <div className="space-y-3">
                    {analytics.curriculum_optimization.learning_gaps.map((gap, i) => (
                      <div key={i} className="p-4 bg-amber-50 border-l-4 border-amber-500 rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold text-gray-900">{gap.concept}</h3>
                          <span className="px-2 py-1 bg-amber-200 text-amber-900 text-xs font-semibold rounded">
                            {gap.frequency} students
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 mb-2">{gap.description}</p>
                        <div className="text-sm text-amber-800 bg-amber-100 p-2 rounded">
                          💡 <strong>Suggestion:</strong> {gap.recommendation}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Score Range Info */}
          <div className="alert-info">
            <h3 className="font-semibold">📈 Score Range</h3>
            <p className="mt-1">
              Scores range from {analytics.stats.min_score.toFixed(1)}% to {analytics.stats.max_score.toFixed(1)}%
            </p>
          </div>
        </>
      ) : analytics && !analytics.has_data ? (
        <div className="alert-info">
          <h3 className="font-semibold">No Graded Submissions</h3>
          <p className="mt-1">
            {analytics.message || 'This problem set has no graded submissions yet.'}
          </p>
        </div>
      ) : null}

      {/* Course Feedback Section */}
      <div className="border-t-4 border-purple-200 pt-8 mt-8">
        <div className="card bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-purple-200 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-3xl">📋</div>
            <h2 className="text-2xl font-bold text-purple-900">Student Course Feedback</h2>
          </div>
          <p className="text-purple-700">
            See what students are saying about your course. Use these insights to improve content, pacing, and teaching effectiveness.
          </p>
        </div>

        {feedbackLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="spinner-lg mb-3"></div>
              <p className="text-gray-600">Loading feedback...</p>
            </div>
          </div>
        ) : feedbackSummary && feedbackSummary.has_data ? (
          <>
            {/* Feedback Insights */}
            {feedbackSummary.insights && feedbackSummary.insights.length > 0 && (
              <div className="card mb-6">
                <h2 className="text-xl font-semibold text-aub-black mb-4">
                  🎯 Key Insights
                </h2>
                <div className="space-y-3">
                  {feedbackSummary.insights.map((insight, i) => (
                    <div
                      key={i}
                      className={`p-4 rounded-lg border-l-4 ${
                        insight.type === 'success' ? 'border-green-500 bg-green-50' :
                        insight.type === 'warning' ? 'border-orange-500 bg-orange-50' :
                        'border-blue-500 bg-blue-50'
                      }`}
                    >
                      <h3 className="font-semibold text-gray-900 mb-1">
                        {insight.type === 'success' ? '✅' : insight.type === 'warning' ? '⚠️' : 'ℹ️'} {insight.title}
                      </h3>
                      <p className="text-sm text-gray-700">{insight.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rating Overview */}
            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="card bg-gradient-to-br from-yellow-50 to-orange-100">
                <div className="text-3xl mb-2">⭐</div>
                <div className="text-3xl font-bold text-aub-black">
                  {feedbackSummary.average_ratings?.overall_rating.toFixed(1)}/5
                </div>
                <div className="text-sm text-gray-600">Overall Rating</div>
                <div className="text-xs text-gray-500 mt-1">
                  {feedbackSummary.total_responses} responses
                </div>
              </div>

              <div className="card bg-gradient-to-br from-blue-50 to-blue-100">
                <div className="text-3xl mb-2">📚</div>
                <div className="text-3xl font-bold text-aub-black">
                  {feedbackSummary.average_ratings?.content_quality.toFixed(1)}/5
                </div>
                <div className="text-sm text-gray-600">Content Quality</div>
              </div>

              <div className="card bg-gradient-to-br from-purple-50 to-purple-100">
                <div className="text-3xl mb-2">👨‍🏫</div>
                <div className="text-3xl font-bold text-aub-black">
                  {feedbackSummary.average_ratings?.instructor_effectiveness.toFixed(1)}/5
                </div>
                <div className="text-sm text-gray-600">Instructor Effectiveness</div>
              </div>
            </div>

            {/* Detailed Ratings */}
            <div className="card mb-6">
              <h2 className="text-xl font-semibold text-aub-black mb-4">
                📊 Detailed Ratings
              </h2>
              <div className="space-y-6">
                {/* Difficulty Level */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Difficulty Level</span>
                    <span className="text-sm text-gray-600">
                      {feedbackSummary.average_ratings?.difficulty_level.toFixed(1)}/5
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-16">Too Easy</span>
                    <div className="flex-1 h-8 bg-gray-200 rounded-full overflow-hidden flex">
                      {[1, 2, 3, 4, 5].map(rating => {
                        const count = feedbackSummary.rating_distribution?.difficulty_level?.[rating] || 0;
                        const total = feedbackSummary.total_responses || 1;
                        const percentage = (count / total) * 100;
                        return (
                          <div
                            key={rating}
                            className={`h-full flex items-center justify-center text-xs font-medium ${
                              rating <= 2 ? 'bg-green-400' :
                              rating === 3 ? 'bg-yellow-400' :
                              'bg-red-400'
                            }`}
                            style={{ width: `${percentage}%` }}
                            title={`${rating} stars: ${count} responses`}
                          >
                            {count > 0 && count}
                          </div>
                        );
                      })}
                    </div>
                    <span className="text-xs text-gray-500 w-16 text-right">Too Hard</span>
                  </div>
                </div>

                {/* Pacing */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Course Pacing</span>
                    <span className="text-sm text-gray-600">
                      {feedbackSummary.average_ratings?.pacing.toFixed(1)}/5
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 w-16">Too Slow</span>
                    <div className="flex-1 h-8 bg-gray-200 rounded-full overflow-hidden flex">
                      {[1, 2, 3, 4, 5].map(rating => {
                        const count = feedbackSummary.rating_distribution?.pacing?.[rating] || 0;
                        const total = feedbackSummary.total_responses || 1;
                        const percentage = (count / total) * 100;
                        return (
                          <div
                            key={rating}
                            className={`h-full flex items-center justify-center text-xs font-medium ${
                              rating <= 2 ? 'bg-blue-400' :
                              rating === 3 ? 'bg-green-400' :
                              'bg-orange-400'
                            }`}
                            style={{ width: `${percentage}%` }}
                            title={`${rating} stars: ${count} responses`}
                          >
                            {count > 0 && count}
                          </div>
                        );
                      })}
                    </div>
                    <span className="text-xs text-gray-500 w-16 text-right">Too Fast</span>
                  </div>
                </div>

                {/* Materials Quality */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Materials Quality</span>
                    <span className="text-sm text-gray-600">
                      {feedbackSummary.average_ratings?.materials_quality.toFixed(1)}/5
                    </span>
                  </div>
                  <div className="h-8 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-400 to-blue-600 flex items-center justify-center text-white text-sm font-medium"
                      style={{ width: `${(feedbackSummary.average_ratings?.materials_quality || 0) * 20}%` }}
                    >
                      {feedbackSummary.average_ratings?.materials_quality.toFixed(1)}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Topics */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              {/* Favorite Topics */}
              {feedbackSummary.top_favorite_topics && feedbackSummary.top_favorite_topics.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    💚 Favorite Topics
                  </h2>
                  <div className="space-y-2">
                    {feedbackSummary.top_favorite_topics.slice(0, 10).map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-green-50 rounded">
                        <span className="text-sm text-gray-800">{item.topic}</span>
                        <span className="px-2 py-1 bg-green-200 text-green-800 text-xs font-semibold rounded">
                          {item.count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Challenging Topics */}
              {feedbackSummary.top_challenging_topics && feedbackSummary.top_challenging_topics.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    🔥 Challenging Topics
                  </h2>
                  <div className="space-y-2">
                    {feedbackSummary.top_challenging_topics.slice(0, 10).map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-2 bg-red-50 rounded">
                        <span className="text-sm text-gray-800">{item.topic}</span>
                        <span className="px-2 py-1 bg-red-200 text-red-800 text-xs font-semibold rounded">
                          {item.count}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Student Comments */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Positive Comments */}
              {feedbackSummary.positive_comments && feedbackSummary.positive_comments.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    ✨ What Worked Well
                  </h2>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {feedbackSummary.positive_comments.map((comment, i) => (
                      <div key={i} className="p-3 bg-green-50 border-l-4 border-green-400 rounded">
                        <p className="text-sm text-gray-800 mb-1">&quot;{comment.comment}&quot;</p>
                        <p className="text-xs text-gray-500">— {comment.student}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Improvement Suggestions */}
              {feedbackSummary.improvement_comments && feedbackSummary.improvement_comments.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold text-aub-black mb-4">
                    🔧 Areas for Improvement
                  </h2>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {feedbackSummary.improvement_comments.map((comment, i) => (
                      <div key={i} className="p-3 bg-orange-50 border-l-4 border-orange-400 rounded">
                        <p className="text-sm text-gray-800 mb-1">&quot;{comment.comment}&quot;</p>
                        <p className="text-xs text-gray-500">— {comment.student}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Additional Suggestions */}
            {feedbackSummary.suggestions && feedbackSummary.suggestions.length > 0 && (
              <div className="card mt-6">
                <h2 className="text-xl font-semibold text-aub-black mb-4">
                  💡 Student Suggestions
                </h2>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {feedbackSummary.suggestions.map((comment, i) => (
                    <div key={i} className="p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
                      <p className="text-sm text-gray-800 mb-1">&quot;{comment.comment}&quot;</p>
                      <p className="text-xs text-gray-500">— {comment.student}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : feedbackSummary && !feedbackSummary.has_data ? (
          <div className="card bg-gray-50">
            <div className="text-center py-8">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">No Feedback Yet</h3>
              <p className="text-gray-600">
                {feedbackSummary.message || 'No students have submitted course feedback yet.'}
              </p>
              <p className="text-sm text-gray-500 mt-4">
                Encourage students to provide feedback at /student/feedback
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
