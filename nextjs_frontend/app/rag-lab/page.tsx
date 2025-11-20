"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");

const buildApiUrl = (path: string) => {
  if (!API_BASE_URL) {
    return path;
  }
  const normalizedBase = API_BASE_URL.endsWith("/")
    ? API_BASE_URL.slice(0, -1)
    : API_BASE_URL;
  return `${normalizedBase}${path}`;
};

type ChapterResponse = {
  chapters: string[];
};

type ChunkPayload = {
  chunk_id: string;
  doc_id?: string;
  formatted: string;
  summary?: string;
  topics?: string[];
  start?: number;
  end?: number;
  score?: number | null;
};

type UploadResponse = {
  success: boolean;
  doc_id: string;
  chunk_count: number;
  chunks: ChunkPayload[];
};

type ChunkListResponse = {
  doc_id: string;
  chunk_count: number;
  chunks: ChunkPayload[];
};

type RagResponse = {
  success: boolean;
  prompt: string;
  answer: string;
  retrieved_chunks: ChunkPayload[];
};

export default function RagLabPage() {
  const [chapters, setChapters] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [docIdInput, setDocIdInput] = useState("");
  const [overwrite, setOverwrite] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [chunkSourceDoc, setChunkSourceDoc] = useState("");
  const [chunks, setChunks] = useState<ChunkPayload[]>([]);

  const [isUploading, setIsUploading] = useState(false);
  const [isFetchingChunks, setIsFetchingChunks] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);

  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [chunkError, setChunkError] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(4);

  const [promptPreview, setPromptPreview] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [retrievedChunks, setRetrievedChunks] = useState<ChunkPayload[]>([]);

  useEffect(() => {
    const fetchChapters = async () => {
      try {
        const res = await fetch(buildApiUrl("/api/py/chapters"));
        if (!res.ok) {
          throw new Error("Failed to load documents");
        }
        const data: ChapterResponse = await res.json();
        setChapters(data.chapters || []);
      } catch (error: any) {
        console.error(error);
      }
    };
    fetchChapters();
  }, []);

  const activeDocId = useMemo(() => {
    return selectedDoc || chunkSourceDoc || "";
  }, [selectedDoc, chunkSourceDoc]);

  const handleUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setUploadError("Please attach a PDF before uploading.");
      return;
    }
    setUploadError(null);
    setUploadMessage("Uploading and chunking your PDF...");
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (docIdInput.trim()) {
        formData.append("doc_id", docIdInput.trim());
      }
      formData.append("overwrite", String(overwrite));

      const res = await fetch(buildApiUrl("/api/py/upload-material"), {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || "Failed to chunk PDF.");
      }
      const data: UploadResponse = await res.json();
      setChunks(data.chunks || []);
      setChunkSourceDoc(data.doc_id);
      setUploadMessage(
        `Stored ${data.chunk_count} chunks for ${data.doc_id}. Ready for questions.`
      );
      setChapters((prev) =>
        prev.includes(data.doc_id) ? prev : [...prev, data.doc_id]
      );
    } catch (error: any) {
      setUploadError(error.message || "Something went wrong.");
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadMessage(null), 4000);
    }
  };

  const loadChunksForDoc = async (docId: string) => {
    if (!docId) {
      setChunkError("Select a document first.");
      return;
    }
    setChunkError(null);
    setIsFetchingChunks(true);
    try {
      const res = await fetch(
        buildApiUrl(`/api/py/documents/${encodeURIComponent(docId)}/chunks`)
      );
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || "Unable to fetch chunks.");
      }
      const data: ChunkListResponse = await res.json();
      setChunks(data.chunks || []);
      setChunkSourceDoc(data.doc_id);
    } catch (error: any) {
      setChunkError(error.message || "Unable to fetch chunks.");
    } finally {
      setIsFetchingChunks(false);
    }
  };

  const handleQuery = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const docId = activeDocId;
    if (!docId) {
      setQueryError("Choose a document (upload one or pick existing).");
      return;
    }
    if (!queryText.trim()) {
      setQueryError("Type a question first.");
      return;
    }
    setQueryError(null);
    setIsQuerying(true);
    setPromptPreview("Building prompt...");
    setRagAnswer("");
    setRetrievedChunks([]);
    try {
      const res = await fetch(buildApiUrl("/api/py/rag-query"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryText.trim(),
          doc_id: docId,
          top_k: topK,
        }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || "RAG query failed.");
      }
      const data: RagResponse = await res.json();
      setPromptPreview(data.prompt || "");
      setRagAnswer(data.answer || "");
      setRetrievedChunks(data.retrieved_chunks || []);
    } catch (error: any) {
      setQueryError(error.message || "Unable to complete RAG query.");
      setPromptPreview("");
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#050b1e] text-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <header className="flex flex-col gap-4 border-b border-white/10 pb-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-pink-300/80">
              RAG debugger
            </p>
            <h1 className="mt-1 text-4xl font-semibold text-white">
              Chunk & Prompt Lab
            </h1>
            <p className="mt-3 max-w-3xl text-base text-slate-300">
              Upload any PDF, inspect the semantic chunks exactly as they are
              embedded, and observe the full Retrieval-Augmented prompt +
              retrieved chunks when you ask a question. Use this page to build
              trust in the pipeline without disturbing the main experience.
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-pink-300/50 px-5 py-2 text-sm font-semibold text-pink-200 transition hover:bg-pink-400/10"
          >
            ← Back to Problem Builder
          </Link>
        </header>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <form
            onSubmit={handleUpload}
            className="rounded-3xl border border-white/5 bg-white/5 p-6 backdrop-blur"
          >
            <h2 className="text-xl font-semibold text-white">
              1. Upload fresh material
            </h2>
            <p className="mt-2 text-sm text-slate-300">
              Chunk any PDF and store it instantly. Re-upload with overwrite to
              refresh a document ID.
            </p>

            <label className="mt-5 block text-sm font-semibold text-slate-200">
              PDF document
              <input
                type="file"
                accept="application/pdf"
                onChange={(event) =>
                  setFile(event.target.files ? event.target.files[0] : null)
                }
                className="mt-2 block w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-white file:mr-4 file:rounded-lg file:border-0 file:bg-pink-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              />
            </label>

            <label className="mt-4 block text-sm font-semibold text-slate-200">
              Custom document ID (optional)
              <input
                type="text"
                value={docIdInput}
                onChange={(event) => setDocIdInput(event.target.value)}
                placeholder="physics-chapter-4"
                className="mt-2 w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm text-white placeholder:text-white/50 focus:border-pink-400/70 focus:outline-none"
              />
            </label>

            <label className="mt-4 flex items-center gap-2 text-sm font-medium text-slate-200">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-white/30 bg-transparent text-pink-500 focus:ring-pink-500"
                checked={overwrite}
                onChange={(event) => setOverwrite(event.target.checked)}
              />
              Overwrite existing document with the same ID
            </label>

            <button
              type="submit"
              disabled={isUploading}
              className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-pink-500 to-rose-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isUploading ? "Chunking..." : "Upload & Chunk"}
            </button>

            {uploadMessage && (
              <p className="mt-3 text-sm text-emerald-300">{uploadMessage}</p>
            )}
            {uploadError && (
              <p className="mt-3 text-sm text-rose-300">{uploadError}</p>
            )}
          </form>

          <div className="rounded-3xl border border-white/5 bg-white/5 p-6 backdrop-blur">
            <h2 className="text-xl font-semibold text-white">
              2. Choose material to interrogate
            </h2>
            <p className="mt-2 text-sm text-slate-300">
              Pick any ingested document to preview its stored chunks and run
              RAG queries.
            </p>

            <label className="mt-4 block text-sm font-semibold text-slate-200">
              Document ID
              <select
                value={selectedDoc}
                onChange={(event) => setSelectedDoc(event.target.value)}
                className="mt-2 w-full rounded-xl border border-white/10 bg-[#0d1224] px-3 py-2 text-sm text-white focus:border-pink-400/70 focus:outline-none"
              >
                <option value="">Select from ingested docs</option>
                {chapters.map((chapter) => (
                  <option key={chapter} value={chapter}>
                    {chapter}
                  </option>
                ))}
              </select>
            </label>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => loadChunksForDoc(selectedDoc)}
                disabled={!selectedDoc || isFetchingChunks}
                className="flex-1 rounded-2xl border border-white/15 px-4 py-2.5 text-sm font-semibold text-white transition hover:border-pink-400/50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isFetchingChunks ? "Loading..." : "Load stored chunks"}
              </button>
              <button
                type="button"
                onClick={() => selectedDoc && setChunkSourceDoc(selectedDoc)}
                className="flex-1 rounded-2xl border border-white/15 px-4 py-2.5 text-sm font-semibold text-white transition hover:border-pink-400/50 disabled:opacity-60"
              >
                Use for questions
              </button>
            </div>

            {chunkSourceDoc && (
              <p className="mt-3 text-sm text-slate-300">
                Currently inspecting:{" "}
                <span className="font-semibold text-white">
                  {chunkSourceDoc}
                </span>
              </p>
            )}

            {chunkError && (
              <p className="mt-3 text-sm text-rose-300">{chunkError}</p>
            )}

            <form onSubmit={handleQuery} className="mt-6 rounded-2xl bg-black/20 p-4">
              <h3 className="text-sm font-semibold uppercase tracking-[0.3em] text-pink-200">
                Ask the AI
              </h3>
              <textarea
                value={queryText}
                onChange={(event) => setQueryText(event.target.value)}
                placeholder="e.g., Explain the derivation of the Euler-Lagrange equation."
                className="mt-3 h-28 w-full rounded-xl border border-white/10 bg-transparent px-3 py-2 text-sm text-white placeholder:text-white/50 focus:border-pink-400/70 focus:outline-none"
              />

              <label className="mt-3 block text-xs font-semibold uppercase tracking-[0.3em] text-slate-300">
                Top K chunks
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={topK}
                  onChange={(event) => {
                    const value = Number(event.target.value);
                    setTopK(Number.isNaN(value) ? 1 : value);
                  }}
                  className="mt-2 w-24 rounded-xl border border-white/10 bg-transparent px-3 py-1.5 text-sm text-white focus:border-pink-400/70 focus:outline-none"
                />
              </label>

              <button
                type="submit"
                disabled={isQuerying}
                className="mt-4 inline-flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-indigo-500 to-blue-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isQuerying ? "Retrieving..." : "Run RAG Query"}
              </button>

              {queryError && (
                <p className="mt-3 text-sm text-rose-300">{queryError}</p>
              )}
            </form>
          </div>
        </div>

        <div className="mt-10 space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="rounded-3xl border border-white/5 bg-black/30 p-5 lg:col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                    Chunk inventory
                  </p>
                  <h3 className="text-2xl font-semibold text-white">
                    Raw chunks sent to the vector DB
                  </h3>
                </div>
                <div className="text-right text-sm text-slate-300">
                  <p>Doc: {chunkSourceDoc || "—"}</p>
                  <p>Chunks: {chunks.length}</p>
                </div>
              </div>
              <div className="mt-5 max-h-[28rem] space-y-4 overflow-y-auto pr-2 text-sm">
                {chunks.length === 0 && (
                  <p className="text-slate-400">
                    Upload a PDF or load an existing document to inspect its
                    chunks.
                  </p>
                )}
                {chunks.map((chunk) => (
                  <div
                    key={chunk.chunk_id}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs uppercase tracking-[0.3em] text-slate-300">
                      <span>{chunk.chunk_id}</span>
                      <span>
                        {chunk.start ?? "?"} – {chunk.end ?? "?"} chars
                      </span>
                    </div>
                    {chunk.summary && (
                      <p className="mt-2 text-sm font-semibold text-white">
                        {chunk.summary}
                      </p>
                    )}
                    {chunk.topics && chunk.topics.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        {chunk.topics.map((topic) => (
                          <span
                            key={topic}
                            className="rounded-full bg-pink-500/20 px-2 py-0.5 text-pink-200"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    )}
                    <pre className="mt-3 max-h-48 overflow-y-auto rounded-xl bg-black/40 p-3 text-xs text-slate-200">
                      <code>{chunk.formatted}</code>
                    </pre>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-3xl border border-white/5 bg-black/30 p-5">
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                Prompt preview
              </p>
              <h3 className="text-2xl font-semibold text-white">
                Full user payload sent to the LLM
              </h3>
              <pre className="mt-5 h-[26rem] overflow-y-auto rounded-2xl bg-[#0d1224] p-4 text-xs leading-relaxed text-slate-200">
                <code>{promptPreview || "Run a query to see the assembled prompt."}</code>
              </pre>
            </div>
          </div>

          <div className="rounded-3xl border border-white/5 bg-black/30 p-6">
            <div className="flex flex-col gap-3 border-b border-white/10 pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                  Retrieved evidence
                </p>
                <h3 className="text-2xl font-semibold text-white">
                  Answer + cosine scores
                </h3>
              </div>
              {ragAnswer && (
                <span className="rounded-full border border-emerald-300/40 px-3 py-1 text-xs font-semibold text-emerald-200">
                  Answer ready
                </span>
              )}
            </div>

            <div className="mt-4 space-y-5">
              {ragAnswer && (
                <div className="rounded-2xl border border-emerald-300/30 bg-emerald-500/10 p-4 text-sm text-emerald-50">
                  {ragAnswer}
                </div>
              )}

              <div className="space-y-4">
                {retrievedChunks.length === 0 && (
                  <p className="text-sm text-slate-400">
                    Run a query to see which chunks were retrieved and their
                    cosine similarity scores.
                  </p>
                )}
                {retrievedChunks.map((chunk) => (
                  <div
                    key={`${chunk.chunk_id}-retrieved`}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs uppercase tracking-[0.3em] text-slate-300">
                      <span>{chunk.chunk_id}</span>
                      <span>
                        score:{" "}
                        {typeof chunk.score === "number"
                          ? chunk.score.toFixed(4)
                          : "n/a"}
                      </span>
                    </div>
                    <pre className="mt-3 max-h-40 overflow-y-auto rounded-xl bg-black/40 p-3 text-xs text-slate-200">
                      <code>{chunk.formatted}</code>
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
