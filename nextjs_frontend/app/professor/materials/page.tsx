'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  getAllDocuments, 
  uploadMaterialWithProgress, 
  deleteMaterial 
} from '@/lib/api';
import type { Material, UploadProgress } from '@/lib/types';

/**
 * Materials Management Page
 * Upload, view, and delete course materials
 */
export default function MaterialsPage() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [customDocId, setCustomDocId] = useState('');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);

  // Load materials
  const loadMaterials = async () => {
    try {
      setLoading(true);
      setError(null);
      const docs = await getAllDocuments();
      setMaterials(docs);
    } catch (err: any) {
      setError(err.message || 'Failed to load materials');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMaterials();
  }, []);

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploadProgress({
      file: selectedFile,
      progress: 0,
      status: 'uploading',
    });

    try {
      await uploadMaterialWithProgress(
        selectedFile,
        customDocId || undefined,
        false,
        (prog) => {
          setUploadProgress((prev) => prev ? { ...prev, progress: prog } : null);
        }
      );

      setUploadProgress((prev) => prev ? { ...prev, status: 'complete' } : null);
      setSelectedFile(null);
      setCustomDocId('');
      
      // Reload materials after upload
      setTimeout(() => {
        loadMaterials();
        setUploadProgress(null);
      }, 2000);
    } catch (err: any) {
      setUploadProgress((prev) => prev ? {
        ...prev,
        status: 'error',
        error: err.message || 'Upload failed',
      } : null);
    }
  };

  // Handle delete
  const handleDelete = async (docId: string) => {
    if (!confirm(`Are you sure you want to delete "${docId}"? This cannot be undone.`)) {
      return;
    }

    try {
      await deleteMaterial(docId);
      loadMaterials();
    } catch (err: any) {
      alert(`Failed to delete: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-aub-black">Course Materials</h1>
        <p className="text-gray-600 mt-2">
          Upload and manage your course PDFs with semantic chunking
        </p>
      </div>

      {/* Upload Section */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Upload New Material
        </h2>

        <div className="space-y-4">
          {/* File Input */}
          <div>
            <label className="label">PDF File</label>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="input"
            />
          </div>

          {/* Custom Doc ID */}
          <div>
            <label className="label">
              Document ID (optional)
            </label>
            <input
              type="text"
              value={customDocId}
              onChange={(e) => setCustomDocId(e.target.value)}
              placeholder="Leave empty to use filename"
              className="input"
            />
            <p className="text-xs text-gray-500 mt-1">
              A unique identifier for this document. If empty, the filename will be used.
            </p>
          </div>

          {/* Progress Bar */}
          {uploadProgress && (
            <div className="space-y-2">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress.progress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {uploadProgress.status === 'uploading' && `Uploading... ${Math.round(uploadProgress.progress)}%`}
                {uploadProgress.status === 'processing' && 'Processing and chunking...'}
                {uploadProgress.status === 'complete' && '✅ Upload complete!'}
                {uploadProgress.status === 'error' && `❌ ${uploadProgress.error}`}
              </p>
            </div>
          )}

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploadProgress?.status === 'uploading'}
            className="btn-primary"
          >
            {uploadProgress?.status === 'uploading' ? 'Uploading...' : 'Upload PDF'}
          </button>
        </div>
      </div>

      {/* Materials List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-aub-black mb-4">
          Uploaded Materials ({materials.length})
        </h2>

        {loading && (
          <div className="text-center py-8">
            <div className="spinner-lg mx-auto mb-3"></div>
            <p className="text-gray-600">Loading materials...</p>
          </div>
        )}

        {error && (
          <div className="alert-error">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && materials.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No materials uploaded yet.</p>
            <p className="text-sm mt-1">Upload a PDF to get started.</p>
          </div>
        )}

        {!loading && !error && materials.length > 0 && (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Document ID</th>
                  <th>Chunks</th>
                  <th>Size</th>
                  <th>Avg Chunk</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {materials.map((material) => (
                  <tr key={material.doc_id}>
                    <td>
                      <span className="font-medium text-gray-900">
                        {material.doc_id}
                      </span>
                    </td>
                    <td>
                      <span className="badge-green">
                        {material.chunk_count} chunks
                      </span>
                    </td>
                    <td className="text-sm text-gray-600">
                      {Math.round(material.total_chars / 1024)} KB
                    </td>
                    <td className="text-sm text-gray-600">
                      {material.avg_chunk_size} chars
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/professor/materials/${encodeURIComponent(material.doc_id)}`}
                          className="text-aub-red hover:text-aub-black text-sm font-medium"
                        >
                          View Chunks
                        </Link>
                        <button
                          onClick={() => handleDelete(material.doc_id)}
                          className="text-error hover:text-red-800 text-sm font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

