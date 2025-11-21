'use client';

import { useState } from 'react';
import Link from 'next/link';

/**
 * Student Problem Sets Page
 * View available problem sets and submissions
 */
export default function StudentProblemSetsPage() {
  // Mock data - in production, this would come from a database
  const [problemSets] = useState([
    {
      id: '1',
      title: 'Thermodynamics Set 1',
      doc_id: 'Chapter_5_Thermodynamics',
      num_problems: 5,
      completed: 5,
      grade: 92,
      due_date: '2024-02-01',
      status: 'graded',
    },
    {
      id: '2',
      title: 'Fluid Mechanics Set 1',
      doc_id: 'Chapter_7_Fluid_Mechanics',
      num_problems: 4,
      completed: 4,
      grade: 85,
      due_date: '2024-02-08',
      status: 'graded',
    },
    {
      id: '3',
      title: 'Heat Transfer Set 2',
      doc_id: 'Chapter_6_Heat_Transfer',
      num_problems: 6,
      completed: 3,
      grade: null,
      due_date: '2024-02-15',
      status: 'in_progress',
    },
  ]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'graded':
        return <span className="badge-success">Graded</span>;
      case 'submitted':
        return <span className="badge-info">Submitted</span>;
      case 'in_progress':
        return <span className="badge-warning">In Progress</span>;
      default:
        return <span className="badge">Not Started</span>;
    }
  };

  const getGradeColor = (grade: number) => {
    if (grade >= 90) return 'text-green-600';
    if (grade >= 80) return 'text-yellow-600';
    if (grade >= 70) return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Problem Sets</h1>
        <p className="text-gray-600 mt-2">
          Complete practice problems and track your progress
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-aub-black">
            {problemSets.length}
          </div>
          <div className="text-sm text-gray-600">Total Sets</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">
            {problemSets.filter((s) => s.status === 'graded').length}
          </div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-yellow-600">
            {problemSets.filter((s) => s.status === 'in_progress').length}
          </div>
          <div className="text-sm text-gray-600">In Progress</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-aub-gray-dark">
            {Math.round(
              problemSets
                .filter((s) => s.grade)
                .reduce((sum, s) => sum + (s.grade || 0), 0) /
                problemSets.filter((s) => s.grade).length
            )}
            %
          </div>
          <div className="text-sm text-gray-600">Avg Grade</div>
        </div>
      </div>

      {/* Problem Sets List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Your Problem Sets
        </h2>

        <div className="space-y-4">
          {problemSets.map((set) => (
            <div
              key={set.id}
              className="border border-gray-200 rounded-aub p-4 hover:border-aub-red transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-gray-900">{set.title}</h3>
                    {getStatusBadge(set.status)}
                  </div>

                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                    <span>
                      {set.completed} / {set.num_problems} problems completed
                    </span>
                    <span>•</span>
                    <span>Due {new Date(set.due_date).toLocaleDateString()}</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="progress-bar mb-2">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${(set.completed / set.num_problems) * 100}%`,
                      }}
                    />
                  </div>

                  {set.grade !== null && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">Grade:</span>
                      <span
                        className={`text-lg font-bold ${getGradeColor(
                          set.grade
                        )}`}
                      >
                        {set.grade}%
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2">
                  <Link
                    href={`/student/problem-sets/${set.id}`}
                    className="btn-primary text-sm text-center"
                  >
                    View Set
                  </Link>
                  {set.status === 'in_progress' && (
                    <button className="btn-secondary text-sm">Continue</button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

