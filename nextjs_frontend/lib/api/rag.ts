/**
 * RAG (Retrieval-Augmented Generation) API
 * Handles AI chatbot queries with document context
 */

import { buildApiUrl, post } from './client';
import type { RAGQueryRequest, RAGResponse, RAGStreamEvent } from '../types';

/**
 * Query the RAG system with a question
 */
export async function ragQuery(request: RAGQueryRequest): Promise<RAGResponse> {
  return post<RAGResponse>('/api/py/rag-query', request);
}

/**
 * Streaming query helper for chat-like UX
 */
export async function streamRagQuery(
  request: RAGQueryRequest,
  onEvent: (event: RAGStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const url = buildApiUrl('/api/py/rag-query/stream');
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok || !response.body) {
    let detail = `HTTP ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || data.error || detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const event = JSON.parse(line) as RAGStreamEvent;
        onEvent(event);
      } catch (err) {
        console.error('Failed to parse stream event', err, line);
      }
    }
  }
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

