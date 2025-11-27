'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

import { getMaterials } from '@/lib/api';
import {
  generateMCQs,
  streamMCQGeneration,
  saveMCQ,
  getSavedMCQs,
  deleteSavedMCQ,
  generateExamPDF,
  downloadExamPDF,
  type MCQ,
  type SavedMCQ,
  type MCQStreamEvent,
} from '@/lib/api/mcqs';

/**
 * MCQ Generation and Exam Creation Page
 * Generate MCQs from chapters, save selected ones, and create exam PDFs
 */
export default function MCQPage() {
  const router = useRouter();

  const [materials, setMaterials] = useState<string[]>([]);
  const [loadingMaterials, setLoadingMaterials] = useState(true);

  // MCQ Generation state
  const [selectedMaterial, setSelectedMaterial] = useState('');
  const [numMCQs, setNumMCQs] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [mcqSet, setMcqSet] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [controllerRef, setControllerRef] = useState<AbortController | null>(null);

  // Saved MCQs state
  const [savedMCQs, setSavedMCQs] = useState<SavedMCQ[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(true);
  const [selectedMCQIds, setSelectedMCQIds] = useState<Set<string>>(new Set());

  // Exam generation state
  const [generatingExam, setGeneratingExam] = useState(false);
  const [examTitle, setExamTitle] = useState('');

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

  // Load saved MCQs
  useEffect(() => {
    async function loadSavedMCQs() {
      try {
        const response = await getSavedMCQs();
        setSavedMCQs(response.mcqs);
      } catch (err: any) {
        console.error('Failed to load saved MCQs:', err);
      } finally {
        setLoadingSaved(false);
      }
    }
    loadSavedMCQs();
  }, []);

  // Handle MCQ generation with streaming
  const handleGenerateMCQs = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedMaterial) {
      setError('Please select a material');
      return;
    }

    // Cancel any existing stream
    if (controllerRef) {
      controllerRef.abort();
    }

    const controller = new AbortController();
    setControllerRef(controller);

    try {
      setGenerating(true);
      setError(null);
      setStatusMessage('');
      setMcqSet(null);

      // Initialize MCQ set structure
      const initialSet: any = {
        doc_id: selectedMaterial,
        analysis: null,
        prompt_info: null,
        num_mcqs: 0,
        mcqs: [],
      };
      setMcqSet(initialSet);

      await streamMCQGeneration(
        selectedMaterial,
        numMCQs,
        (event: MCQStreamEvent) => {
          if (event.type === 'status') {
            setStatusMessage(event.message);
            if (event.complete && event.step === 4) {
              setGenerating(false);
              setControllerRef(null);
            }
          } else if (event.type === 'prompt_info') {
            setMcqSet((prev: any) => ({
              ...prev,
              prompt_info: event.data,
            }));
          } else if (event.type === 'analysis') {
            setMcqSet((prev: any) => ({
              ...prev,
              analysis: event.data,
            }));
          } else if (event.type === 'mcq') {
            // Add new MCQ to the list as it arrives
            setMcqSet((prev: any) => ({
              ...prev,
              mcqs: [...prev.mcqs, event.data],
              num_mcqs: prev.mcqs.length + 1,
            }));
          } else if (event.type === 'done') {
            setGenerating(false);
            setControllerRef(null);
            setStatusMessage('Generation complete!');
          } else if (event.type === 'error') {
            setError(event.message);
            setGenerating(false);
            setControllerRef(null);
          }
        },
        controller.signal
      );
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to generate MCQs');
        setGenerating(false);
      }
      setControllerRef(null);
    }
  };

  // Handle stop generation
  const handleStopGeneration = () => {
    if (controllerRef) {
      controllerRef.abort();
      setControllerRef(null);
      setGenerating(false);
      setStatusMessage('Generation stopped');
    }
  };

  // Handle saving MCQ
  const handleSaveMCQ = async (mcq: MCQ, chapter: string) => {
    try {
      const response = await saveMCQ(mcq, chapter);
      // Reload saved MCQs
      const updated = await getSavedMCQs();
      setSavedMCQs(updated.mcqs);
      alert('MCQ saved successfully!');
    } catch (err: any) {
      alert(`Failed to save MCQ: ${err.message}`);
    }
  };

  // Handle deleting saved MCQ
  const handleDeleteMCQ = async (mcqId: string) => {
    if (!confirm('Are you sure you want to delete this MCQ?')) return;

    try {
      await deleteSavedMCQ(mcqId);
      // Reload saved MCQs
      const updated = await getSavedMCQs();
      setSavedMCQs(updated.mcqs);
      // Remove from selection if selected
      setSelectedMCQIds((prev) => {
        const next = new Set(prev);
        next.delete(mcqId);
        return next;
      });
    } catch (err: any) {
      alert(`Failed to delete MCQ: ${err.message}`);
    }
  };

  // Handle exam generation
  const handleGenerateExam = async () => {
    if (selectedMCQIds.size === 0) {
      alert('Please select at least one MCQ to include in the exam');
      return;
    }

    try {
      setGeneratingExam(true);
      const mcqIds = Array.from(selectedMCQIds);
      const blob = await generateExamPDF(mcqIds, examTitle || undefined);
      const filename = examTitle
        ? `${examTitle.replace(/[^a-z0-9]/gi, '_')}.pdf`
        : `exam_${new Date().toISOString().split('T')[0]}.pdf`;
      downloadExamPDF(blob, filename);
      alert('Exam PDF generated and downloaded successfully!');
    } catch (err: any) {
      alert(`Failed to generate exam: ${err.message}`);
    } finally {
      setGeneratingExam(false);
    }
  };

  // Toggle MCQ selection
  const toggleMCQSelection = (mcqId: string) => {
    setSelectedMCQIds((prev) => {
      const next = new Set(prev);
      if (next.has(mcqId)) {
        next.delete(mcqId);
      } else {
        next.add(mcqId);
      }
      return next;
    });
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <button
          onClick={() => router.back()}
          className="text-aub-red hover:text-aub-black text-sm font-medium mb-2"
        >
          ← Back
        </button>
        <h1 className="text-3xl font-bold text-aub-black">MCQ Generation & Exam Creation</h1>
        <p className="text-gray-600 mt-2">
          Generate multiple choice questions from your course materials, save your favorites, and create exam PDFs
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* MCQ Generation Panel */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Generate MCQs
          </h2>

          <form onSubmit={handleGenerateMCQs} className="space-y-4">
            <div>
              <label className="label">Select Chapter</label>
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

            <div>
              <label className="label">Number of MCQs</label>
              <input
                type="number"
                min={1}
                max={25}
                value={numMCQs}
                onChange={(e) => setNumMCQs(Math.max(1, Number(e.target.value) || 1))}
                disabled={generating}
                className="input"
              />
            </div>

            {error && (
              <div className="alert-error text-sm">{error}</div>
            )}

            {statusMessage && generating && (
              <div className="bg-blue-50 border border-blue-200 rounded-aub p-3 text-sm text-blue-800">
                <div className="flex items-center gap-2">
                  <span className="spinner"></span>
                  <span>{statusMessage}</span>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={generating || loadingMaterials || materials.length === 0}
                className="btn-primary flex-1"
              >
                {generating ? (
                  <>
                    <span className="spinner mr-2"></span>
                    Generating...
                  </>
                ) : (
                  'Generate MCQs'
                )}
              </button>
              {generating && (
                <button
                  type="button"
                  onClick={handleStopGeneration}
                  className="btn-secondary"
                >
                  Stop
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Saved MCQs & Exam Generation Panel */}
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Saved MCQs & Exam Generation
          </h2>

          {loadingSaved ? (
            <div className="text-center py-8">
              <div className="spinner-lg mx-auto mb-3"></div>
              <p className="text-gray-600">Loading saved MCQs...</p>
            </div>
          ) : savedMCQs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No saved MCQs yet.</p>
              <p className="text-sm mt-2">Generate and save MCQs to create an exam.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-aub-beige p-3 rounded-aub">
                <p className="text-sm font-semibold">
                  {savedMCQs.length} saved MCQ{savedMCQs.length !== 1 ? 's' : ''}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedMCQIds.size} selected for exam
                </p>
              </div>

              <div>
                <label className="label">Exam Title (Optional)</label>
                <input
                  type="text"
                  value={examTitle}
                  onChange={(e) => setExamTitle(e.target.value)}
                  placeholder="e.g., Midterm Exam 2024"
                  className="input"
                />
              </div>

              <button
                onClick={handleGenerateExam}
                disabled={generatingExam || selectedMCQIds.size === 0}
                className="btn-primary w-full"
              >
                {generatingExam ? (
                  <>
                    <span className="spinner mr-2"></span>
                    Generating PDF...
                  </>
                ) : (
                  `📄 Generate Exam PDF (${selectedMCQIds.size} questions)`
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Generated MCQs Display */}
      {mcqSet && (
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Generated MCQs from {mcqSet.doc_id}
          </h2>

          <div className="space-y-6">
            {mcqSet.mcqs.map((mcq: MCQ, index: number) => (
              <div key={`${mcqSet.doc_id}-${mcq.id}-${index}`} className="border border-gray-200 rounded-aub p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="badge text-xs capitalize">{mcq.difficulty}</span>
                      <span className="badge-info text-xs">{mcq.topic}</span>
                      {mcq.question_type && (
                        <span 
                          className={`text-xs px-2 py-1 rounded font-semibold ${
                            mcq.question_type === 'analytical' 
                              ? 'bg-purple-100 text-purple-700 border border-purple-300' 
                              : 'bg-blue-100 text-blue-700 border border-blue-300'
                          }`}
                          title={mcq.question_type === 'analytical' ? 'Analytical question - tests deeper understanding and reasoning' : 'Direct question - tests factual knowledge and recall'}
                        >
                          {mcq.question_type === 'analytical' ? '🧠 Analytical' : '📝 Direct'}
                        </span>
                      )}
                    </div>
                    <div className="font-medium text-gray-900 mb-3 prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {`${index + 1}. ${mcq.question}`}
                      </ReactMarkdown>
                    </div>
                  </div>
                  <button
                    onClick={() => handleSaveMCQ(mcq, mcqSet.doc_id)}
                    className="btn-secondary text-sm ml-4"
                  >
                    💾 Save
                  </button>
                </div>

                <div className="space-y-2 ml-4">
                  {Object.entries(mcq.options).map(([key, value]) => (
                    <div key={key} className="text-sm prose prose-sm max-w-none">
                      <span className="font-semibold">{key}.</span>{' '}
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {value}
                      </ReactMarkdown>
                    </div>
                  ))}
                </div>

                <details className="mt-3 ml-4">
                  <summary className="cursor-pointer text-sm text-gray-600">
                    Show answer & explanation
                  </summary>
                  <div className="mt-2 p-3 bg-green-50 rounded-aub text-sm">
                    <p className="font-semibold mb-1">
                      Correct Answer: {mcq.correct_answer}
                    </p>
                    <div className="text-gray-700 prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {mcq.explanation}
                      </ReactMarkdown>
                    </div>
                  </div>
                </details>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Saved MCQs List */}
      {savedMCQs.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Saved MCQs ({savedMCQs.length})
          </h2>

          <div className="space-y-4">
            {savedMCQs.map((savedMCQ) => (
              <div
                key={savedMCQ.id}
                className={`border rounded-aub p-4 ${
                  selectedMCQIds.has(savedMCQ.id)
                    ? 'border-aub-red bg-red-50'
                    : 'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <input
                        type="checkbox"
                        checked={selectedMCQIds.has(savedMCQ.id)}
                        onChange={() => toggleMCQSelection(savedMCQ.id)}
                        className="w-4 h-4 text-aub-red"
                      />
                      <span className="badge text-xs capitalize">
                        {savedMCQ.mcq.difficulty}
                      </span>
                      <span className="badge-info text-xs">{savedMCQ.mcq.topic}</span>
                      {savedMCQ.mcq.question_type && (
                        <span 
                          className={`text-xs px-2 py-1 rounded font-semibold ${
                            savedMCQ.mcq.question_type === 'analytical' 
                              ? 'bg-purple-100 text-purple-700 border border-purple-300' 
                              : 'bg-blue-100 text-blue-700 border border-blue-300'
                          }`}
                          title={savedMCQ.mcq.question_type === 'analytical' ? 'Analytical question - tests deeper understanding and reasoning' : 'Direct question - tests factual knowledge and recall'}
                        >
                          {savedMCQ.mcq.question_type === 'analytical' ? '🧠 Analytical' : '📝 Direct'}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        from {savedMCQ.chapter}
                      </span>
                    </div>
                    <div className="font-medium text-gray-900 mb-2 prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {savedMCQ.mcq.question}
                      </ReactMarkdown>
                    </div>
                    <div className="text-sm text-gray-600 space-y-1">
                      {Object.entries(savedMCQ.mcq.options).map(([key, value]) => (
                        <div key={key} className="prose prose-sm max-w-none">
                          <span className="font-semibold">{key}.</span>{' '}
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkMath]}
                            rehypePlugins={[rehypeKatex]}
                          >
                            {value}
                          </ReactMarkdown>
                        </div>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteMCQ(savedMCQ.id)}
                    className="btn-secondary text-sm ml-4 text-red-600 hover:text-red-800"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

