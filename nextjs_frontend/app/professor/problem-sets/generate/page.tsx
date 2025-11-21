'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { getMaterials, generateProblemSet, exportProblemSet, downloadProblemSet } from '@/lib/api';
import type { ProblemSet } from '@/lib/types';

/**
 * Generate Problem Set Page
 * Create AI-powered problem sets from course materials
 */
export default function GenerateProblemSetPage() {
  const router = useRouter();

  const [materials, setMaterials] = useState<string[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);

  // Form state
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [numProblems, setNumProblems] = useState(5);
  const [checkQuality, setCheckQuality] = useState(true);

  // Generation state
  const [generating, setGenerating] = useState(false);
  const [problemSet, setProblemSet] = useState<ProblemSet | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Export state
  const [exporting, setExporting] = useState(false);

  // Load available materials
  useEffect(() => {
    async function loadMaterials() {
      try {
        const docs = await getMaterials();
        setMaterials(docs);
        if (docs.length > 0) {
          setSelectedMaterial(docs[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load materials');
      } finally {
        setLoadingMaterials(false);
      }
    }
    loadMaterials();
  }, []);

  // Handle generation
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedMaterial) {
      setError('Please select a material');
      return;
    }

    try {
      setGenerating(true);
      setError(null);
      setProblemSet(null);

      const result = await generateProblemSet({
        doc_id: selectedMaterial,
        num_problems: numProblems,
        check_quality: checkQuality,
      });

      setProblemSet(result);
    } catch (err: any) {
      setError(err.message || 'Failed to generate problem set');
    } finally {
      setGenerating(false);
    }
  };

  // Handle export
  const handleExport = async (format: 'markdown' | 'json' | 'problems_only') => {
    if (!problemSet) return;

    try {
      setExporting(true);
      const { content, filename } = await exportProblemSet(problemSet, format);
      downloadProblemSet(content, filename);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <button
          onClick={() => router.back()}
          className="text-aub-red hover:text-aub-black text-sm font-medium mb-2"
        >
          ← Back to Problem Sets
        </button>
        <h1 className="text-3xl font-bold text-aub-black">Generate Problem Set</h1>
        <p className="text-gray-600 mt-2">
          Create AI-powered problems and solutions from your course materials
        </p>
      </div>

      {/* Generation Form */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Configuration
          </h2>

          <form onSubmit={handleGenerate} className="space-y-4">
            {/* Material Selection */}
            <div>
              <label className="label">Select Material</label>
              <select
                value={selectedMaterial}
                onChange={(e) => setSelectedMaterial(e.target.value)}
                disabled={loadingMaterials || generating}
                className="select"
              >
                {loadingMaterials && (
                  <option value="">Loading materials...</option>
                )}
                {!loadingMaterials && materials.length === 0 && (
                  <option value="">No materials available</option>
                )}
                {materials.map((material) => (
                  <option key={material} value={material}>
                    {material}
                  </option>
                ))}
              </select>
            </div>

            {/* Number of Problems */}
            <div>
              <label className="label">Number of Problems</label>
              <input
                type="number"
                min={1}
                max={25}
                value={numProblems}
                onChange={(e) => setNumProblems(Math.max(1, Number(e.target.value) || 1))}
                disabled={generating}
                className="input"
              />
            </div>

            {/* Quality Check */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="checkQuality"
                checked={checkQuality}
                onChange={(e) => setCheckQuality(e.target.checked)}
                disabled={generating}
                className="w-4 h-4 text-aub-red focus:ring-aub-red border-gray-300 rounded"
              />
              <label htmlFor="checkQuality" className="text-sm font-medium text-gray-700">
                Include quality review
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="alert-error text-sm">
                {error}
              </div>
            )}

            {/* Generate Button */}
            <button
              type="submit"
              disabled={generating || loadingMaterials || materials.length === 0}
              className="btn-primary w-full"
            >
              {generating ? (
                <>
                  <span className="spinner mr-2"></span>
                  Generating... (this may take a minute)
                </>
              ) : (
                'Generate Problem Set'
              )}
            </button>
          </form>
        </div>

        {/* Status Panel */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Status
          </h2>

          {!problemSet && !generating && (
            <div className="text-center py-8 text-gray-500">
              <p>Configure your settings and click Generate</p>
            </div>
          )}

          {generating && (
            <div className="text-center py-8">
              <div className="spinner-lg mx-auto mb-3"></div>
              <p className="text-gray-600">
                Analyzing material and generating problems...
              </p>
              <p className="text-sm text-gray-500 mt-2">
                This usually takes 30-60 seconds
              </p>
            </div>
          )}

          {problemSet && (
            <div className="space-y-4">
              <div className="alert-success">
                <p className="font-semibold">✅ Problem set generated successfully!</p>
                <p className="text-sm mt-1">
                  {problemSet.num_problems} problems created
                </p>
              </div>

              {/* Export Options */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  Export Options
                </h3>
                <div className="space-y-2">
                  <button
                    onClick={() => handleExport('markdown')}
                    disabled={exporting}
                    className="btn-secondary w-full"
                  >
                    📄 Export as Markdown (with solutions)
                  </button>
                  <button
                    onClick={() => handleExport('problems_only')}
                    disabled={exporting}
                    className="btn-secondary w-full"
                  >
                    📝 Export Problems Only
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    disabled={exporting}
                    className="btn-secondary w-full"
                  >
                    💾 Export as JSON
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Problem Set Preview */}
      {problemSet && (
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Preview
          </h2>

          {/* Metadata */}
          <div className="bg-aub-beige p-4 rounded-aub mb-4">
            <p className="text-sm">
              <span className="font-semibold">Material:</span> {problemSet.doc_id}
            </p>
            {problemSet.analysis?.topics && (
              <p className="text-sm mt-1">
                <span className="font-semibold">Topics:</span>{' '}
                {problemSet.analysis.topics.join(', ')}
              </p>
            )}
          </div>

          {/* Problems */}
          <div className="space-y-4">
            {problemSet.problem_set.map((item, index) => {
              const problem = item.problem;
              const solution = item.solution;

              return (
                <details key={index} className="border border-gray-200 rounded-aub p-4">
                  <summary className="cursor-pointer font-medium text-gray-900">
                    Problem {index + 1}: {problem.statement}
                  </summary>
                  <div className="mt-3 space-y-3 text-sm">
                    {problem.given && problem.given.length > 0 && (
                      <div>
                        <p className="font-semibold">Given:</p>
                        <ul className="list-disc pl-5 mt-1">
                          {problem.given.map((g, i) => (
                            <li key={i}>{g}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {solution && (
                      <div>
                        <p className="font-semibold mb-2">Solution:</p>
                        <div className="bg-gray-50 p-3 rounded-aub prose prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                          >
                            {solution}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                </details>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

