'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSystemStats, getAllDocuments } from '@/lib/api';

/**
 * Professor Dashboard
 * Overview page with quick stats and actions
 */
export default function ProfessorDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load dashboard data
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [systemStats, documents] = await Promise.all([
          getSystemStats(),
          getAllDocuments(),
        ]);
        setStats({ 
          ...systemStats, 
          documents,
          total_documents: documents.length 
        });
      } catch (err: any) {
        console.error('Failed to load dashboard data:', err);
        setError(err.message || 'Failed to load dashboard data');
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
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <h3 className="font-semibold">Error loading dashboard</h3>
        <p className="mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Section */}
      <div className="card bg-aub-red text-white p-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Welcome back, Professor!</h1>
        <p className="text-white/90">
          Manage your courses, generate problem sets, and track student performance
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid md:grid-cols-4 gap-6">
        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">📚</div>
          <div className="text-2xl font-bold text-aub-red">
            {stats?.total_documents || 0}
          </div>
          <div className="text-sm text-gray-600">Course Materials</div>
        </div>

        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">🧩</div>
          <div className="text-2xl font-bold text-aub-red">
            {stats?.total_chunks || 0}
          </div>
          <div className="text-sm text-gray-600">Content Chunks</div>
        </div>

        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-2xl font-bold text-aub-red">
            {stats?.avg_chunks_per_document || 0}
          </div>
          <div className="text-sm text-gray-600">Avg Chunks/Doc</div>
        </div>

        <div className="card hover:shadow-aub-lg transition-shadow">
          <div className="text-3xl mb-2">💾</div>
          <div className="text-2xl font-bold text-aub-red">
            {Math.round((stats?.total_characters || 0) / 1024)} KB
          </div>
          <div className="text-sm text-gray-600">Total Content</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-aub-black mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-3 gap-6">
          <Link href="/professor/materials">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                📤 Upload Material
              </h3>
              <p className="text-sm text-gray-600">
                Add new course PDFs and visualize semantic chunking
              </p>
            </div>
          </Link>

          <Link href="/professor/problem-sets/generate">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                ✨ Generate Problem Set
              </h3>
              <p className="text-sm text-gray-600">
                Create AI-powered problem sets from materials
              </p>
            </div>
          </Link>

          <Link href="/professor/analytics">
            <div className="card-hover">
              <h3 className="text-lg font-semibold text-aub-black mb-2">
                📊 View Analytics
              </h3>
              <p className="text-sm text-gray-600">
                Track performance and identify trends
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Materials */}
      {stats?.documents && stats.documents.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold text-aub-black mb-4">
            Recent Materials
          </h2>
          <div className="space-y-3">
            {stats.documents.slice(0, 5).map((doc: any, i: number) => (
              <div 
                key={i} 
                className="flex items-center justify-between py-3 border-b last:border-0"
              >
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{doc.doc_id}</div>
                  <div className="text-sm text-gray-600">
                    {doc.chunk_count} chunks · {Math.round(doc.total_chars / 1024)} KB
                  </div>
                </div>
                <Link 
                  href={`/professor/materials/${encodeURIComponent(doc.doc_id)}`}
                  className="text-aub-red hover:text-aub-red-dark text-sm font-medium"
                >
                  View →
                </Link>
              </div>
            ))}
          </div>
          {stats.documents.length > 5 && (
            <div className="mt-4 text-center">
              <Link href="/professor/materials" className="text-aub-red hover:text-aub-red-dark text-sm font-medium">
                View all materials →
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

