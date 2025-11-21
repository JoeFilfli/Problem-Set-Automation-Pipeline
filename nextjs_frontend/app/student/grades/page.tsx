'use client';

import { useState } from 'react';

/**
 * Student Grades Page
 * View all grades and feedback
 */
export default function StudentGradesPage() {
  // Mock data - in production, this would come from a database
  const [grades] = useState([
    {
      id: '1',
      problem_set: 'Thermodynamics Set 1',
      problem_number: 1,
      score: 18,
      max_score: 20,
      percentage: 90,
      submitted: '2024-01-28',
      graded: '2024-01-29',
      feedback: 'Excellent work! Clear methodology and correct answer.',
    },
    {
      id: '2',
      problem_set: 'Thermodynamics Set 1',
      problem_number: 2,
      score: 19,
      max_score: 20,
      percentage: 95,
      submitted: '2024-01-28',
      graded: '2024-01-29',
      feedback: 'Perfect! Great attention to detail.',
    },
    {
      id: '3',
      problem_set: 'Fluid Mechanics Set 1',
      problem_number: 1,
      score: 16,
      max_score: 20,
      percentage: 80,
      submitted: '2024-02-05',
      graded: '2024-02-06',
      feedback: 'Good approach, but check your unit conversions.',
    },
  ]);

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

  const avgGrade =
    grades.reduce((sum, g) => sum + g.percentage, 0) / grades.length;

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">My Grades</h1>
        <p className="text-gray-600 mt-2">
          View your submissions and feedback
        </p>
      </div>

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
            {Math.round((grades.filter((g) => g.percentage >= 90).length / grades.length) * 100)}% of submissions
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
                <th>Details</th>
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
                  <td className="text-center">{grade.problem_number}</td>
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
                      {getGradeLetter(grade.percentage)}
                    </span>
                  </td>
                  <td className="text-sm text-gray-600">
                    {new Date(grade.submitted).toLocaleDateString()}
                  </td>
                  <td>
                    <button className="text-aub-red hover:text-aub-black text-sm font-medium">
                      View Feedback
                    </button>
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

        <div className="space-y-4">
          {grades.slice(0, 3).map((grade) => (
            <div
              key={grade.id}
              className="border border-gray-200 rounded-aub p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {grade.problem_set} - Problem {grade.problem_number}
                  </h4>
                  <p className="text-sm text-gray-500">
                    Graded on {new Date(grade.graded).toLocaleDateString()}
                  </p>
                </div>
                <div
                  className={`px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(
                    grade.percentage
                  )}`}
                >
                  {grade.percentage}%
                </div>
              </div>
              <p className="text-sm text-gray-700">{grade.feedback}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

