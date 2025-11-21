'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { getProblemSet } from '@/lib/api/submissions';

/**
 * Professor Problem Set View
 * View problem set details
 */
export default function ProfessorProblemSetViewPage() {
  const params = useParams();
  const router = useRouter();
  const setId = params.setId as string;

  const [problemSet, setProblemSet] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Load problem set from backend
  useEffect(() => {
    async function loadData() {
      const data = await getProblemSet(setId);
      setProblemSet(data);
      setLoading(false);
    }
    
    loadData();
  }, [setId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading problem set...</p>
        </div>
      </div>
    );
  }

  if (!problemSet) {
    return (
      <div className="text-center py-12">
        <p className="text-lg text-gray-600">Problem set not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <button
          onClick={() => router.back()}
          className="text-aub-red hover:text-aub-black text-sm font-medium mb-2"
        >
          ← Back to Problem Sets
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-aub-black">{problemSet.title}</h1>
            <p className="text-gray-600 mt-1">
              {problemSet.num_problems} problems · Created {new Date(problemSet.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex gap-2">
            <button className="btn-secondary">
              📤 Export Set
            </button>
            <button 
              onClick={() => router.push(`/professor/problem-sets/${setId}/submissions`)}
              className="btn-primary"
            >
              View Submissions
            </button>
          </div>
        </div>
      </div>

      {/* Problem Set Info */}
      <div className="card bg-aub-beige">
        <h3 className="font-semibold text-aub-black mb-2">Problem Set Information</h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Source Material:</span>
            <p className="font-medium text-gray-900">{problemSet.doc_id}</p>
          </div>
          <div>
            <span className="text-gray-600">Total Problems:</span>
            <p className="font-medium text-gray-900">{problemSet.num_problems}</p>
          </div>
          <div>
            <span className="text-gray-600">Status:</span>
            <p className="font-medium text-green-600">Published</p>
          </div>
        </div>
      </div>

      {/* Problems */}
      <div className="space-y-6">
        {problemSet.problem_set.map((item, index) => {
          const problem = item.problem;
          const solution = item.solution;

          return (
            <div key={problem.id} className="card">
              {/* Problem Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-bold text-aub-black">
                      Problem {index + 1}
                    </h2>
                    <span className="badge text-xs capitalize">
                      {problem.difficulty}
                    </span>
                    <span className="badge-info text-xs">
                      {problem.topic}
                    </span>
                  </div>
                  <p className="text-lg text-gray-800">{problem.statement}</p>
                </div>
              </div>

              {/* Given Information */}
              {problem.given && problem.given.length > 0 && (
                <div className="mb-4 p-4 bg-aub-beige rounded-aub">
                  <h3 className="text-sm font-semibold text-aub-black mb-2">
                    Given:
                  </h3>
                  <ul className="space-y-1">
                    {problem.given.map((item, i) => (
                      <li key={i} className="text-sm text-gray-700">
                        • {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Required */}
              {problem.required && problem.required.length > 0 && (
                <div className="mb-4 p-4 bg-blue-50 rounded-aub border border-blue-200">
                  <h3 className="text-sm font-semibold text-blue-900 mb-2">
                    Required:
                  </h3>
                  <ul className="space-y-1">
                    {problem.required.map((item, i) => (
                      <li key={i} className="text-sm text-blue-800">
                        • {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Solution */}
              <div className="p-4 bg-green-50 border border-green-200 rounded-aub">
                <h3 className="text-sm font-semibold text-green-900 mb-2">
                  Model Solution:
                </h3>
                <div className="prose prose-sm max-w-none text-gray-800">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                  >
                    {solution}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

