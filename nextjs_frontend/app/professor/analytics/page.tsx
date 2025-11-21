'use client';

import { useState, useEffect } from 'react';
import { getSystemStats, getAllDocuments } from '@/lib/api';

/**
 * Analytics Dashboard
 * View system statistics and insights
 */
export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [systemStats, documents] = await Promise.all([
          getSystemStats(),
          getAllDocuments(),
        ]);
        setStats({ ...systemStats, documents });
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner-lg mb-3"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error loading analytics</h3>
        <p className="mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Analytics Dashboard</h1>
        <p className="text-gray-600 mt-2">
          System statistics and insights
        </p>
      </div>

      {/* Overview Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        <div className="card">
          <div className="text-3xl mb-2">📚</div>
          <div className="text-2xl font-bold text-aub-black">
            {stats.total_documents}
          </div>
          <div className="text-sm text-gray-600">Total Documents</div>
        </div>

        <div className="card">
          <div className="text-3xl mb-2">🧩</div>
          <div className="text-2xl font-bold text-aub-black">
            {stats.total_chunks}
          </div>
          <div className="text-sm text-gray-600">Total Chunks</div>
        </div>

        <div className="card">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-2xl font-bold text-aub-black">
            {stats.avg_chunk_size}
          </div>
          <div className="text-sm text-gray-600">Avg Chunk Size (chars)</div>
        </div>

        <div className="card">
          <div className="text-3xl mb-2">📈</div>
          <div className="text-2xl font-bold text-aub-black">
            {stats.avg_chunks_per_document}
          </div>
          <div className="text-sm text-gray-600">Avg Chunks/Document</div>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Content Statistics
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Total Characters:</span>
              <span className="font-medium">{stats.total_characters.toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Min Chunk Size:</span>
              <span className="font-medium">{stats.min_chunk_size} chars</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Max Chunk Size:</span>
              <span className="font-medium">{stats.max_chunk_size} chars</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-600">Total Size:</span>
              <span className="font-medium">
                {Math.round(stats.total_characters / 1024)} KB
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-aub-black mb-4">
            Document Breakdown
          </h2>
          {stats.documents && stats.documents.length > 0 ? (
            <div className="space-y-2">
              {stats.documents.slice(0, 5).map((doc: any, i: number) => (
                <div key={i} className="flex justify-between py-2 border-b last:border-0">
                  <span className="text-gray-700 text-sm truncate flex-1 mr-4">
                    {doc.doc_id}
                  </span>
                  <span className="text-sm font-medium whitespace-nowrap">
                    {doc.chunk_count} chunks
                  </span>
                </div>
              ))}
              {stats.documents.length > 5 && (
                <p className="text-sm text-gray-500 text-center pt-2">
                  + {stats.documents.length - 5} more documents
                </p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No documents yet</p>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="alert-info">
        <h3 className="font-semibold">📊 About Analytics</h3>
        <p className="mt-1">
          These statistics show how your content is being processed and stored. 
          Semantic chunking ensures optimal context retrieval for AI-powered features.
        </p>
      </div>
    </div>
  );
}

