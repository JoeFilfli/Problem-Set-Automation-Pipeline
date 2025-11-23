'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getAllProblemSets, countSubmissions } from '@/lib/api/submissions';

/**
 * Student Problem Sets Page
 * View available problem sets and submissions
 */
export default function StudentProblemSetsPage() {
  const [problemSets, setProblemSets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Load problem sets from backend
  useEffect(() => {
    const loadProblemSets = async () => {
      const allSets = await getAllProblemSets();
      
      // Enrich with submission data
      const enrichedPromises = allSets.map(async (set: any) => {
        const submissionCounts = await countSubmissions(set.id);
        
        // Count completed problems (those with at least one submission)
        const completedCount = Object.keys(submissionCounts.byProblem).length;
        
        // Calculate average grade from graded submissions
        let totalScore = 0;
        let gradedCount = 0;
        Object.values(submissionCounts.byProblem).forEach((problemStats: any) => {
          if (problemStats.graded > 0) {
            gradedCount += problemStats.graded;
          }
        });
        
        const avgGrade = gradedCount > 0 ? null : null; // Grade calculation needs submission grade data
        
        return {
          id: set.id,
          title: set.title || `${set.doc_id} - Problem Set`,
          doc_id: set.doc_id,
          num_problems: set.num_problems,
          completed: completedCount,
          grade: avgGrade,
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
          status: gradedCount >= set.num_problems ? 'graded' : (completedCount > 0 ? 'in_progress' : 'not_started'),
        };
      });
      
      const enriched = await Promise.all(enrichedPromises);
      setProblemSets(enriched);
      setLoading(false);
    };
    
    loadProblemSets();
  }, []);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading problem sets...</p>
        </div>
      </div>
    );
  }

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

        {problemSets.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg mb-2">No problem sets available yet</p>
            <p className="text-sm">Your professor hasn&apos;t created any problem sets.</p>
          </div>
        )}

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

