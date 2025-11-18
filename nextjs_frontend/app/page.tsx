"use client";

import { useEffect, useState } from "react";

type ChapterResponse = {
  chapters: string[];
};

type ProblemSetResponse = {
  success: boolean;
  problem_set: any;
};

export default function Home() {
  const [chapters, setChapters] = useState<string[]>([]);
  const [selectedChapter, setSelectedChapter] = useState<string>("");
  const [numProblems, setNumProblems] = useState<number>(5);
  const [checkQuality, setCheckQuality] = useState<boolean>(true);

  const [isLoadingChapters, setIsLoadingChapters] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const [problemSet, setProblemSet] = useState<any | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load available chapters on first render
  useEffect(() => {
    const fetchChapters = async () => {
      try {
        setIsLoadingChapters(true);
        setErrorMessage(null);
        setStatusMessage("Loading available chapters from the backend...");

        const res = await fetch("/api/py/chapters");

        if (!res.ok) {
          // Try to surface backend error details if available
          let detail = "";
          try {
            const data = await res.json();
            detail =
              (data && (data.detail || data.error || JSON.stringify(data))) ||
              "";
          } catch {
            // ignore JSON parse errors
          }

          throw new Error(
            `Could not load chapters (HTTP ${res.status}). ${detail}`.trim()
          );
        }

        const data: ChapterResponse = await res.json();
        setChapters(data.chapters || []);
        if (data.chapters && data.chapters.length > 0) {
          setSelectedChapter(data.chapters[0]);
        }
        setStatusMessage(null);
      } catch (err: any) {
        console.error("Error loading chapters:", err);
        setErrorMessage(
          err?.message ||
            "Unable to load chapters. Please confirm the FastAPI backend is running."
        );
      } finally {
        setIsLoadingChapters(false);
      }
    };

    fetchChapters();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedChapter) {
      setErrorMessage("Please select a chapter before generating problems.");
      return;
    }

    try {
      setIsGenerating(true);
      setErrorMessage(null);
      setProblemSet(null);

      setStatusMessage("Thinking deeply about your chapter content...");

      const payload = {
        doc_id: selectedChapter,
        num_problems: numProblems,
        check_quality: checkQuality,
      };

      const res = await fetch("/api/py/generate-problem-set", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let backendDetail = "";
        try {
          const data = await res.json();
          backendDetail =
            data?.detail ||
            data?.error ||
            (typeof data === "string" ? data : JSON.stringify(data));
        } catch {
          // ignore JSON parse errors
        }

        throw new Error(
          backendDetail
            ? `Backend error (HTTP ${res.status}): ${backendDetail}`
            : `Request failed with status ${res.status}.`
        );
      }

      const data: ProblemSetResponse = await res.json();

      if (!data.success) {
        throw new Error("Backend responded but did not mark success=true.");
      }

      setProblemSet(data.problem_set);
      setStatusMessage("Problem set generated successfully.");
    } catch (err: any) {
      console.error("Error generating problem set:", err);
      setErrorMessage(
        err?.message ||
          "Something went wrong while generating the problem set. Please check the backend logs."
      );
      setStatusMessage(null);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-50">
      <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-10 md:px-8 md:py-14">
        {/* Header */}
        <header className="flex flex-col gap-3 border-b border-slate-800 pb-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl">
              AI Problem Set Studio
            </h1>
            <p className="mt-2 max-w-xl text-sm text-slate-300 md:text-base">
              Choose a chapter from your course materials and let the AI
              generate a tailored problem set with detailed solutions.
            </p>
          </div>
          <div className="rounded-full bg-slate-900/70 px-4 py-1 text-xs font-medium text-slate-300 ring-1 ring-slate-700/70">
            FastAPI + Next.js • RAG-powered pipeline
          </div>
        </header>

        {/* Controls + status */}
        <section className="grid gap-6 md:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
          <form
            onSubmit={handleGenerate}
            className="space-y-4 rounded-2xl bg-slate-900/70 p-5 shadow-lg shadow-slate-950/60 ring-1 ring-slate-800"
          >
            <h2 className="text-lg font-semibold text-slate-100">
              Generate a problem set
            </h2>

            {/* Chapter selector */}
            <div className="space-y-1.5">
              <label
                htmlFor="chapter"
                className="text-xs font-medium uppercase tracking-wide text-slate-400"
              >
                Chapter
              </label>
              <div className="relative">
                <select
                  id="chapter"
                  value={selectedChapter}
                  onChange={(e) => setSelectedChapter(e.target.value)}
                  disabled={isLoadingChapters || isGenerating}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-3 py-2.5 pr-9 text-sm text-slate-50 outline-none ring-0 transition focus:border-cyan-400 focus:ring-1 focus:ring-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {chapters.length === 0 && (
                    <option value="">
                      {isLoadingChapters
                        ? "Loading chapters…"
                        : "No chapters available"}
                    </option>
                  )}
                  {chapters.map((chapter) => (
                    <option key={chapter} value={chapter}>
                      {chapter}
                    </option>
                  ))}
                </select>
                <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs text-slate-400">
                  ▼
                </span>
              </div>
              <p className="text-xs text-slate-400">
                These are the PDF documents you ingested into the RAG vector
                store.
              </p>
            </div>

            {/* Number of problems */}
            <div className="space-y-1.5">
              <label
                htmlFor="numProblems"
                className="text-xs font-medium uppercase tracking-wide text-slate-400"
              >
                Number of problems
              </label>
              <input
                id="numProblems"
                type="number"
                min={1}
                max={25}
                value={numProblems}
                onChange={(e) =>
                  setNumProblems(Math.max(1, Number(e.target.value) || 1))
                }
                disabled={isGenerating}
                className="w-32 rounded-xl border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm text-slate-50 outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-500 disabled:cursor-not-allowed disabled:opacity-60"
              />
            </div>

            {/* Quality check toggle */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCheckQuality((v) => !v)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full border border-slate-700 transition ${
                  checkQuality
                    ? "bg-cyan-500/80 shadow-[0_0_0_1px_rgba(34,211,238,0.8)]"
                    : "bg-slate-800"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-slate-950 shadow transition ${
                    checkQuality ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
              <div className="space-y-0.5">
                <p className="text-sm font-medium text-slate-100">
                  Run quality checks
                </p>
                <p className="text-xs text-slate-400">
                  Ask the AI to review each problem and solution for clarity and
                  correctness.
                </p>
              </div>
            </div>

            {/* Generate button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={
                  isGenerating || isLoadingChapters || chapters.length === 0
                }
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500 px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-900/50 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isGenerating ? (
                  <>
                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-950/70 border-t-transparent" />
                    Generating problem set…
                  </>
                ) : (
                  <>Generate problems</>
                )}
              </button>
            </div>
          </form>

          {/* Status + feedback */}
          <div className="space-y-3 rounded-2xl bg-slate-900/60 p-5 ring-1 ring-slate-800">
            <h2 className="text-sm font-semibold text-slate-100">
              Status & messages
            </h2>

            {statusMessage && (
              <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100">
                {isGenerating ? (
                  <p>
                    {statusMessage} This may take a minute while the agents
                    analyze your chapter, generate problems, write solutions,
                    and check quality.
                  </p>
                ) : (
                  <p>{statusMessage}</p>
                )}
              </div>
            )}

            {errorMessage && (
              <div className="rounded-xl border border-rose-500/50 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
                <p className="font-semibold">Something went wrong</p>
                <p className="mt-1 text-[0.7rem] leading-snug">{errorMessage}</p>
                <ul className="mt-2 list-disc pl-4 text-[0.7rem] text-rose-100/80">
                  <li>Confirm the FastAPI backend is running.</li>
                  <li>
                    Check the terminal running FastAPI for any detailed error
                    logs.
                  </li>
                  <li>
                    Ensure the vector store has been ingested and the selected
                    chapter exists.
                  </li>
                </ul>
              </div>
            )}

            {!statusMessage && !errorMessage && (
              <p className="text-xs text-slate-400">
                When you click <span className="font-semibold">Generate</span>,
                you&apos;ll see live status messages here while the backend
                agents do their work.
              </p>
            )}
          </div>
        </section>

        {/* Problem set viewer */}
        <section className="space-y-3 rounded-2xl bg-slate-900/70 p-5 ring-1 ring-slate-800">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-slate-100">
              Generated problem set
            </h2>
            {problemSet && (
              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                {problemSet.num_problems ??
                  problemSet.problem_set?.length ??
                  0}{" "}
                problems
              </span>
            )}
          </div>

          {!problemSet && (
            <p className="text-sm text-slate-400">
              Your generated problems, solutions, and quality checks will appear
              here. Start by selecting a chapter and clicking{" "}
              <span className="font-semibold">Generate problems</span>.
            </p>
          )}

          {problemSet && (
            <div className="space-y-4 text-sm">
              {/* Simple summary */}
              <div className="rounded-xl bg-slate-950/60 p-3 text-xs text-slate-300 ring-1 ring-slate-800/60">
                <p>
                  <span className="font-semibold text-slate-100">
                    Chapter:
                  </span>{" "}
                  {problemSet.doc_id}
                </p>
                {problemSet.analysis?.topics && (
                  <p className="mt-1">
                    <span className="font-semibold text-slate-100">
                      Topics:
                    </span>{" "}
                    {problemSet.analysis.topics.slice(0, 6).join(", ")}
                    {problemSet.analysis.topics.length > 6 ? "…" : ""}
                  </p>
                )}
              </div>

              {/* Problems list */}
              <div className="space-y-3">
                {(problemSet.problem_set || []).map(
                  (item: any, index: number) => {
                    const problem = item.problem ?? item;
                    const solution = item.solution;
                    const quality = item.quality;

                    return (
                      <details
                        key={index}
                        className="group rounded-xl bg-slate-950/70 p-3 ring-1 ring-slate-800/70"
                      >
                        <summary className="flex cursor-pointer list-none items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                              Problem {index + 1}
                            </p>
                            <p className="mt-1 text-sm font-medium text-slate-50">
                              {problem.statement?.slice(0, 140) ||
                                "Untitled problem"}
                              {problem.statement &&
                              problem.statement.length > 140
                                ? "…"
                                : ""}
                            </p>
                            <div className="mt-1 flex flex-wrap gap-2 text-[0.65rem] text-slate-300">
                              {problem.topic && (
                                <span className="rounded-full bg-slate-800 px-2 py-0.5">
                                  Topic: {problem.topic}
                                </span>
                              )}
                              {problem.difficulty && (
                                <span className="rounded-full bg-slate-800 px-2 py-0.5 capitalize">
                                  Difficulty: {problem.difficulty}
                                </span>
                              )}
                            </div>
                          </div>
                          <span className="mt-1 text-xs text-slate-400 group-open:rotate-90 transition-transform">
                            ▶
                          </span>
                        </summary>

                        <div className="mt-3 space-y-2 border-t border-slate-800 pt-3 text-xs leading-relaxed text-slate-200">
                          {problem.given && problem.given.length > 0 && (
                            <div>
                              <p className="font-semibold text-slate-100">
                                Given:
                              </p>
                              <ul className="mt-1 list-disc pl-4 text-slate-200/90">
                                {problem.given.map(
                                  (g: string, i: number) => (
                                    <li key={i}>{g}</li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}

                          {problem.required && problem.required.length > 0 && (
                            <div>
                              <p className="font-semibold text-slate-100">
                                Required:
                              </p>
                              <ul className="mt-1 list-disc pl-4 text-slate-200/90">
                                {problem.required.map(
                                  (r: string, i: number) => (
                                    <li key={i}>{r}</li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}

                          {solution && (
                            <div>
                              <p className="font-semibold text-slate-100">
                                Solution (raw text from AI):
                              </p>
                              <pre className="mt-1 max-h-64 overflow-auto rounded-lg bg-slate-950/90 p-3 text-[0.7rem] text-slate-200 ring-1 ring-slate-800/80">
                                {solution}
                              </pre>
                            </div>
                          )}

                          {quality && (
                            <div className="rounded-lg bg-slate-900/80 p-2 ring-1 ring-slate-800">
                              <p className="text-[0.7rem] font-semibold text-slate-100">
                                Quality check
                              </p>
                              <p className="mt-1 text-[0.7rem] text-slate-200">
                                Overall:{" "}
                                <span className="font-semibold capitalize">
                                  {quality.overall_quality ?? "unknown"}
                                </span>
                              </p>
                              {quality.issues && quality.issues.length > 0 && (
                                <div className="mt-1">
                                  <p className="text-[0.7rem] font-medium text-slate-100">
                                    Issues:
                                  </p>
                                  <ul className="mt-1 list-disc pl-4 text-[0.7rem] text-slate-200/90">
                                    {quality.issues.map(
                                      (q: string, i: number) => (
                                        <li key={i}>{q}</li>
                                      )
                                    )}
                                  </ul>
                                </div>
                              )}
                              {quality.suggestions &&
                                quality.suggestions.length > 0 && (
                                  <div className="mt-1">
                                    <p className="text-[0.7rem] font-medium text-slate-100">
                                      Suggestions:
                                    </p>
                                    <ul className="mt-1 list-disc pl-4 text-[0.7rem] text-slate-200/90">
                                      {quality.suggestions.map(
                                        (s: string, i: number) => (
                                          <li key={i}>{s}</li>
                                        )
                                      )}
                                    </ul>
                                  </div>
                                )}
                            </div>
                          )}
                        </div>
                      </details>
                    );
                  }
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
