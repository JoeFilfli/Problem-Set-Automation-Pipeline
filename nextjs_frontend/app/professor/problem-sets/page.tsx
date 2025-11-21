'use client';

import { useState } from 'react';
import Link from 'next/link';

/**
 * Problem Sets Page
 * List and manage generated problem sets
 * Note: This is a simplified version. In production, you'd store problem sets in a database.
 */
export default function ProblemSetsPage() {
  // Mock data - in production, this would come from a database
  const [problemSets] = useState([
    {
      id: '1',
      doc_id: 'Chapter_5_Thermodynamics',
      num_problems: 5,
      created_at: '2024-01-15',
      topics: ['Heat Transfer', 'Entropy', 'Cycles'],
    },
    {
      id: '2',
      doc_id: 'Chapter_7_Fluid_Mechanics',
      num_problems: 4,
      created_at: '2024-01-14',
      topics: ['Bernoulli', 'Viscosity', 'Flow Rate'],
    },
  ]);

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
                    </div>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {set.topics.map((topic, i) => (
                        <span key={i} className="badge-green">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="btn-secondary text-sm">
                      View
                    </button>
                    <button className="btn-secondary text-sm">
                      Export
                    </button>
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
          Each set includes problems, solutions, and quality reviews.
        </p>
      </div>
    </div>
  );
}

