'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getAllProblemSets, countSubmissions } from '@/lib/api/submissions';

/**
 * Problem Sets Page
 * List and manage generated problem sets
 */
export default function ProblemSetsPage() {
  const [problemSets, setProblemSets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Load problem sets from backend
  useEffect(() => {
    const loadProblemSets = async () => {
      const allSets = await getAllProblemSets();

      // Enrich with submission counts
      const enrichedPromises = allSets.map(async (set: any) => {
        const submissionCounts = await countSubmissions(set.id);

        return {
          id: set.id,
          doc_id: set.doc_id,
          num_problems: set.num_problems,
          created_at: set.created_at,
          topics: set.analysis?.topics || [],
          submissions: submissionCounts.total,
          graded: submissionCounts.graded,
        };
      });

      const enriched = await Promise.all(enrichedPromises);
      setProblemSets(enriched);
      setLoading(false);
    };

    loadProblemSets();
  }, []);



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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-aub-black">Problem Sets</h1>
          <p className="text-gray-600 mt-2">
            Generate and manage AI-powered problem sets
          </p>
        </div>
        <Link href="/professor/problem-sets/generate" className="btn-primary">
          ✨ Generate New Set
        </Link>
      </div>

      {/* Problem Sets List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Generated Problem Sets ({problemSets.length})
        </h2>

        {problemSets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No problem sets generated yet.</p>
            <Link href="/professor/problem-sets/generate" className="text-aub-red hover:text-aub-black mt-2 inline-block">
              Create your first problem set →
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {problemSets.map((set) => (
              <div key={set.id} className="border border-gray-200 rounded-aub p-4 hover:border-aub-red transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{set.doc_id}</h3>
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                      <span>{set.num_problems} problems</span>
                      <span>·</span>
                      <span>Created {new Date(set.created_at).toLocaleDateString()}</span>
                      <span>·</span>
                      <span className="text-blue-600">{set.submissions} submissions</span>
                      <span>·</span>
                      <span className={set.graded === set.submissions ? 'text-green-600' : 'text-orange-600'}>
                        {set.graded}/{set.submissions} graded
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {set.topics.map((topic: string, i: number) => (
                        <span key={i} className="badge-green">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Link
                      href={`/professor/problem-sets/${set.id}`}
                      className="btn-secondary text-sm text-center"
                    >
                      View Set
                    </Link>
                    <Link
                      href={`/professor/problem-sets/${set.id}/submissions`}
                      className="btn-primary text-sm text-center"
                    >
                      Grade ({set.submissions})
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Info Box */}
      <div className="alert-info">
        <h3 className="font-semibold">💡 Tip</h3>
        <p className="mt-1">
          Problem sets are generated from your uploaded course materials using AI.
          Each set includes problems, solutions, and quality reviews. Students can submit
          their solutions, and you can grade them automatically using AI.
        </p>
      </div>
    </div>
  );
}
