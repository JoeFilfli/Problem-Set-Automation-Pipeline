'use client';

import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { getAllProblemSets, getAllSubmissionsForSet } from '@/lib/api/submissions';

/**
 * Student Grades Page
 * View all grades and feedback
 */
export default function StudentGradesPage() {
  const [grades, setGrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedFeedback, setExpandedFeedback] = useState<Set<string>>(new Set());
  const studentName = 'Current Student'; // In production, get from auth

  // Load all graded submissions
  useEffect(() => {
    async function loadGrades() {
      try {
        // Get all problem sets
        const problemSets = await getAllProblemSets();

        // Get all submissions for each problem set
        const allGrades: any[] = [];

        for (const set of problemSets) {
          const submissions = await getAllSubmissionsForSet(set.id);

          // Filter to current student's submissions that are graded
          const studentSubmissions = submissions.filter(
            (sub: any) => sub.student_name === studentName && sub.graded && sub.grade
          );

          // Transform to grade format
          studentSubmissions.forEach((sub: any) => {
            const grade = sub.grade;
            if (grade && grade.summary) {
              allGrades.push({
                id: sub.id,
                problem_set: set.title || set.doc_id,
                problem_set_id: set.id,
                problem_id: sub.problem_id,
                score: grade.summary.score || 0,
                max_score: grade.summary.max_score || 100,
                percentage: grade.summary.percentage || 0,
                grade_letter: grade.summary.grade || 'N/A',
                submitted: sub.submitted_at,
                graded: sub.submitted_at, // Backend doesn't track separate graded time yet
                feedback: grade.feedback || 'No feedback provided',
              });
            }
          });
        }

        setGrades(allGrades);
      } catch (error) {
        console.error('Error loading grades:', error);
      } finally {
        setLoading(false);
      }
    }

    loadGrades();
  }, [studentName]);

  const getGradeColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-600 bg-green-50';
    if (percentage >= 80) return 'text-yellow-600 bg-yellow-50';
    if (percentage >= 70) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getGradeLetter = (percentage: number) => {
    if (percentage >= 90) return 'A';
    if (percentage >= 85) return 'A-';
    if (percentage >= 80) return 'B+';
    if (percentage >= 75) return 'B';
    if (percentage >= 70) return 'B-';
    if (percentage >= 65) return 'C+';
    if (percentage >= 60) return 'C';
    return 'D';
  };

  const avgGrade = grades.length > 0
    ? grades.reduce((sum, g) => sum + g.percentage, 0) / grades.length
    : 0;

  const toggleFeedback = (gradeId: string) => {
    const newExpanded = new Set(expandedFeedback);
    if (newExpanded.has(gradeId)) {
      newExpanded.delete(gradeId);
    } else {
      newExpanded.add(gradeId);
    }
    setExpandedFeedback(newExpanded);
  };

  const truncateFeedback = (feedback: string, maxLength: number = 200) => {
    if (feedback.length <= maxLength) return feedback;
    return feedback.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading grades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">My Grades</h1>
        <p className="text-gray-600 mt-2">
          View your submissions and feedback
        </p>
      </div>

      {grades.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-lg text-gray-600 mb-2">No graded submissions yet</p>
          <p className="text-sm text-gray-500">
            Complete problem sets and wait for your professor to grade them
          </p>
        </div>
      ) : (
        <>
          {/* Overall Stats */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-2xl font-bold text-aub-black">
                {Math.round(avgGrade)}%
              </div>
              <div className="text-sm text-gray-600 mt-1">Overall Average</div>
              <div className="text-lg font-semibold text-aub-gray-dark mt-2">
                Grade: {getGradeLetter(avgGrade)}
              </div>
            </div>

            <div className="card text-center">
              <div className="text-2xl font-bold text-green-600">
                {grades.filter((g) => g.percentage >= 90).length}
              </div>
              <div className="text-sm text-gray-600 mt-1">A Grades</div>
              <div className="text-xs text-gray-500 mt-2">
                {grades.length > 0
                  ? Math.round((grades.filter((g) => g.percentage >= 90).length / grades.length) * 100)
                  : 0}% of submissions
              </div>
            </div>

            <div className="card text-center">
              <div className="text-2xl font-bold text-aub-black">
                {grades.length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Total Submissions</div>
              <div className="text-xs text-gray-500 mt-2">All graded</div>
            </div>
          </div>

          {/* Grades Table */}
          <div className="card">
            <h2 className="text-xl font-semibold text-aub-black mb-4">
              Submission History
            </h2>

            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Problem Set</th>
                    <th>Problem #</th>
                    <th>Score</th>
                    <th>Percentage</th>
                    <th>Grade</th>
                    <th>Submitted</th>
                  </tr>
                </thead>
                <tbody>
                  {grades.map((grade) => (
                    <tr key={grade.id}>
                      <td>
                        <span className="font-medium text-gray-900">
                          {grade.problem_set}
                        </span>
                      </td>
                      <td className="text-center">{grade.problem_id}</td>
                      <td>
                        <span className="text-sm">
                          {grade.score} / {grade.max_score}
                        </span>
                      </td>
                      <td>
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium ${getGradeColor(
                            grade.percentage
                          )}`}
                        >
                          {grade.percentage}%
                        </span>
                      </td>
                      <td>
                        <span className="font-bold text-aub-gray-dark">
                          {grade.grade_letter}
                        </span>
                      </td>
                      <td className="text-sm text-gray-600">
                        {new Date(grade.submitted).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Feedback */}
          <div className="card">
            <h2 className="text-xl font-semibold text-aub-black mb-4">
              Recent Feedback
            </h2>

            <div className="space-y-3">
              {grades.slice(0, 5).map((grade) => {
                const isExpanded = expandedFeedback.has(grade.id);
                const feedbackPreview = truncateFeedback(grade.feedback);
                const hasLongFeedback = grade.feedback.length > 200;

                return (
                  <div
                    key={grade.id}
                    className="border border-gray-200 rounded-aub overflow-hidden hover:border-aub-red transition-colors"
                  >
                    {/* Header */}
                    <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 text-sm">
                          {grade.problem_set}
                        </h4>
                        <div className="flex items-center gap-3 mt-1">
                          <span className="text-xs text-gray-600">
                            Problem {grade.problem_id}
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-600">
                            {new Date(grade.graded).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div
                          className={`px-3 py-1 rounded-full text-sm font-bold ${getGradeColor(
                            grade.percentage
                          )}`}
                        >
                          {grade.percentage}%
                        </div>
                        {hasLongFeedback && (
                          <button
                            onClick={() => toggleFeedback(grade.id)}
                            className="text-aub-red hover:text-aub-black font-medium text-sm transition-colors"
                          >
                            {isExpanded ? '▼ Collapse' : '▶ Expand'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Feedback Content */}
                    <div className="px-4 py-3">
                      <div className="prose prose-sm max-w-none text-gray-700 [&_.katex]:text-base [&_.katex-display]:my-2">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {(isExpanded || !hasLongFeedback
                            ? grade.feedback
                            : feedbackPreview
                          ).replace(/\\\[/g, '$$').replace(/\\\]/g, '$$').replace(/\\\(/g, '$').replace(/\\\)/g, '$')}
                        </ReactMarkdown>
                      </div>
                      {hasLongFeedback && !isExpanded && (
                        <button
                          onClick={() => toggleFeedback(grade.id)}
                          className="text-aub-red hover:text-aub-black text-sm font-medium mt-2"
                        >
                          Read full feedback →
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {grades.length > 5 && (
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-600">
                  Showing 5 most recent feedback items. View all in Submission History above.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
