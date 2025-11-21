'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getDocumentChunks } from '@/lib/api';
import type { Chunk } from '@/lib/types';

/**
 * Document Chunks Viewer
 * View all semantic chunks for a specific document
 */
export default function DocumentChunksPage() {
  const params = useParams();
  const router = useRouter();
  const docId = decodeURIComponent(params.docId as string);

  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load chunks
  useEffect(() => {
    async function loadChunks() {
      try {
        setLoading(true);
        setError(null);
        const data = await getDocumentChunks(docId);
        setChunks(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load chunks');
      } finally {
        setLoading(false);
      }
    }
    loadChunks();
  }, [docId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading chunks...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error loading chunks</h3>
        <p className="mt-1">{error}</p>
        <button onClick={() => router.back()} className="btn-primary mt-4">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.back()}
            className="text-aub-red hover:text-aub-black text-sm font-medium mb-2"
          >
            ← Back to Materials
          </button>
          <h1 className="text-3xl font-bold text-aub-black">{docId}</h1>
          <p className="text-gray-600 mt-1">
            {chunks.length} semantic chunks
          </p>
        </div>
      </div>

      {/* Chunks List */}
      <div className="space-y-4">
        {chunks.map((chunk, index) => (
          <div key={chunk.chunk_id} className="card">
            {/* Chunk Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-aub-black">
                  Chunk {index + 1} · {chunk.chunk_id}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Characters {chunk.start} - {chunk.end} ({chunk.end - chunk.start} chars)
                </p>
              </div>
            </div>

            {/* Summary */}
            {chunk.summary && (
              <div className="mb-3 p-3 bg-aub-beige rounded-aub">
                <h4 className="text-xs font-semibold text-gray-700 mb-1">
                  Summary
                </h4>
                <p className="text-sm text-gray-600">{chunk.summary}</p>
              </div>
            )}

            {/* Topics */}
            {chunk.topics && chunk.topics.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {chunk.topics.map((topic, i) => (
                  <span key={i} className="badge-gold">
                    {topic}
                  </span>
                ))}
              </div>
            )}

            {/* Content */}
            <div className="bg-gray-50 p-4 rounded-aub border border-gray-200">
              <h4 className="text-xs font-semibold text-gray-700 mb-2">
                Content
              </h4>
              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-sans">
                {chunk.formatted}
              </pre>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

