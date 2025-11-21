/**
 * RAG (Retrieval-Augmented Generation) API
 * Handles AI chatbot queries with document context
 */

import { post } from './client';
import type { RAGQueryRequest, RAGResponse } from '../types';

/**
 * Query the RAG system with a question
 */
export async function ragQuery(request: RAGQueryRequest): Promise<RAGResponse> {
  return post<RAGResponse>('/api/py/rag-query', request);
}

/**
 * Search across all documents or specific documents
 */
export async function searchDocuments(
  query: string,
  docIds?: string[],
  topK: number = 10
): Promise<{
  query: string;
  total_results: number;
  results: any[];
}> {
  return post<{
    success: boolean;
    query: string;
    total_results: number;
    results: any[];
  }>('/api/py/search', {
    query,
    doc_ids: docIds,
    top_k: topK,
  });
}

