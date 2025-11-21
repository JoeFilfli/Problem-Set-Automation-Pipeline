/**
 * Materials API
 * Handles course material uploads, retrieval, and management
 */

import { get, post, postFormData, del, uploadWithProgress } from './client';
import type {
  Material,
  Chunk,
  UploadResponse,
  ChunksResponse,
  ApiResponse,
} from '../types';

/**
 * Get list of all materials (chapters)
 */
export async function getMaterials(): Promise<string[]> {
  const response = await get<{ chapters: string[] }>('/api/py/chapters');
  return response.chapters || [];
}

/**
 * Get detailed list of all documents with metadata
 */
export async function getAllDocuments(): Promise<Material[]> {
  const response = await get<{ success: boolean; documents: Material[] }>(
    '/api/py/documents'
  );
  return response.documents || [];
}

/**
 * Get chunks for a specific document
 */
export async function getDocumentChunks(docId: string): Promise<Chunk[]> {
  const response = await get<ChunksResponse>(
    `/api/py/documents/${encodeURIComponent(docId)}/chunks`
  );
  return response.chunks || [];
}

/**
 * Upload a PDF material
 */
export async function uploadMaterial(
  file: File,
  docId?: string,
  overwrite: boolean = false
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (docId) {
    formData.append('doc_id', docId);
  }
  
  formData.append('overwrite', String(overwrite));

  return postFormData<UploadResponse>('/api/py/upload-material', formData);
}

/**
 * Upload a PDF material with progress tracking
 */
export async function uploadMaterialWithProgress(
  file: File,
  docId?: string,
  overwrite: boolean = false,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (docId) {
    formData.append('doc_id', docId);
  }
  
  formData.append('overwrite', String(overwrite));

  return uploadWithProgress<UploadResponse>(
    '/api/py/upload-material',
    formData,
    onProgress
  );
}

/**
 * Delete a document and all its chunks
 */
export async function deleteMaterial(docId: string): Promise<void> {
  await del<ApiResponse<void>>(`/api/py/documents/${encodeURIComponent(docId)}`);
}

/**
 * Search across documents
 */
export async function searchMaterials(
  query: string,
  topK: number = 10,
  docIds?: string[]
): Promise<Chunk[]> {
  const response = await post<{
    success: boolean;
    results: Chunk[];
  }>('/api/py/search', {
    query,
    top_k: topK,
    doc_ids: docIds,
  });
  
  return response.results || [];
}

/**
 * Get system statistics
 */
export async function getSystemStats(): Promise<{
  total_documents: number;
  total_chunks: number;
  total_characters: number;
  avg_chunk_size: number;
  min_chunk_size: number;
  max_chunk_size: number;
  avg_chunks_per_document: number;
}> {
  const response = await get<{
    success: boolean;
    statistics: any;
  }>('/api/py/stats');
  
  return response.statistics;
}

