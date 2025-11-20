"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

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

type ProblemSetResponse = {
  success: boolean;
  problem_set: any;
};

const markdownComponents: Components = {
  h3: ({ node, ...props }) => (
    <h3
      className="mt-4 text-base font-semibold text-[#2c1b14]"
      {...props}
    />
  ),
  h4: ({ node, ...props }) => (
    <h4
      className="mt-3 text-sm font-semibold text-[#5c0f17]"
      {...props}
    />
  ),
  p: ({ node, ...props }) => (
    <p className="mt-2 text-sm leading-relaxed text-[#3e2b22]" {...props} />
  ),
  ul: ({ node, ...props }) => (
    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-[#3e2b22]" {...props} />
  ),
  ol: ({ node, ...props }) => (
    <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-[#3e2b22]" {...props} />
  ),
  li: ({ node, ...props }) => <li {...props} />,
  strong: ({ node, ...props }) => (
    <strong className="font-semibold text-[#2c1b14]" {...props} />
  ),
  blockquote: ({ node, ...props }) => (
    <blockquote
      className="my-3 border-l-4 border-[#f5c2b4] bg-[#fff7f2] px-4 py-2 text-sm italic text-[#5c0f17]"
      {...props}
    />
  ),
  code({
    node,
    inline,
    className,
    children,
    ...props
  }: any) {
    if (inline) {
      return (
        <code
          className="rounded bg-[#f9ece1] px-1.5 py-0.5 text-[0.75rem] text-[#5c0f17]"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <pre className="my-3 overflow-x-auto rounded-lg bg-[#2c1b14] p-3 text-[0.75rem] text-white">
        <code {...props}>{children}</code>
      </pre>
    );
  },
};

const normalizeSolutionMarkdown = (text?: string | null) => {
  if (!text) return "";
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\\times/g, "×")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
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
        setStatusMessage("Gathering your course chapters…");

        const res = await fetch(buildApiUrl("/api/py/chapters"));

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
            "We couldn't load your chapters just yet. Please refresh or try again in a moment."
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

      setStatusMessage("Preparing your personalised practice set…");

      const payload = {
        doc_id: selectedChapter,
        num_problems: numProblems,
        check_quality: checkQuality,
      };

      const res = await fetch(buildApiUrl("/api/py/generate-problem-set"), {
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
      setStatusMessage("Your practice set is ready to view.");
    } catch (err: any) {
      console.error("Error generating problem set:", err);
      setErrorMessage(
        err?.message ||
          "We had trouble preparing the set. Please try again or choose another chapter."
      );
      setStatusMessage(null);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f7f3ec] text-[#2c1b14]">
      <div className="mx-auto flex max-w-5xl flex-col gap-10 px-4 py-10 md:px-8 md:py-14">
        {/* Hero */}
        <header className="rounded-3xl bg-gradient-to-br from-[#5c0f17] via-[#7d1420] to-[#a6192e] px-6 py-8 text-rose-50 shadow-xl shadow-[#5c0f171a] md:px-10">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-100/80">
            American University of Beirut
          </p>
          <h1 className="mt-3 text-3xl font-semibold leading-tight md:text-4xl">
            AUB Learning Companion
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-rose-100 md:text-base">
            Select a course chapter and receive a ready-to-review problem set
            with guided solutions, written in the warm, student-first tone used
            across campus support services.
          </p>
          <div className="mt-5 flex flex-wrap gap-3 text-xs">
            <span className="rounded-full bg-white/15 px-3 py-1 font-semibold uppercase tracking-wide">
              For students & faculty
            </span>
            <span className="rounded-full bg-white/15 px-3 py-1 font-semibold uppercase tracking-wide">
              Powered by AUB Libraries
            </span>
          </div>
        </header>

        {/* Controls + status */}
        <section className="grid gap-6 md:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <form
            onSubmit={handleGenerate}
            className="space-y-5 rounded-3xl bg-white p-6 shadow-xl shadow-rose-100/70 ring-1 ring-rose-100"
          >
            <h2 className="text-lg font-semibold text-[#5c0f17]">
              Create a tailored practice set
            </h2>

            {/* Chapter selector */}
            <div className="space-y-1.5">
              <label
                htmlFor="chapter"
                className="text-xs font-semibold uppercase tracking-wide text-[#8b1b26]/80"
              >
                Chapter
              </label>
              <div className="relative">
                <select
                  id="chapter"
                  value={selectedChapter}
                  onChange={(e) => setSelectedChapter(e.target.value)}
                  disabled={isLoadingChapters || isGenerating}
                  className="w-full rounded-xl border border-[#d8c9bb] bg-[#fdfbf7] px-3 py-2.5 pr-9 text-sm text-[#2c1b14] outline-none transition focus:border-[#a6192e] focus:ring-1 focus:ring-[#a6192e] disabled:cursor-not-allowed disabled:opacity-60"
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
              <p className="text-xs text-[#6b4b3a]">
                These files mirror the official course packets on Moodle and in the Engineering Library.
              </p>
            </div>

            {/* Number of problems */}
            <div className="space-y-1.5">
              <label
                htmlFor="numProblems"
                className="text-xs font-semibold uppercase tracking-wide text-[#8b1b26]/80"
              >
                Number of practice questions
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
                className="w-32 rounded-xl border border-[#d8c9bb] bg-[#fdfbf7] px-3 py-2 text-sm text-[#2c1b14] outline-none focus:border-[#a6192e] focus:ring-1 focus:ring-[#a6192e] disabled:cursor-not-allowed disabled:opacity-60"
              />
            </div>

            {/* Quality check toggle */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCheckQuality((v) => !v)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full border border-[#d8c9bb] transition ${
                  checkQuality ? "bg-[#a6192e]" : "bg-[#e7dcd1]"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition ${
                    checkQuality ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
              <div className="space-y-0.5">
                <p className="text-sm font-medium text-[#2b1c17]">
                  Include a gentle quality review
                </p>
                <p className="text-xs text-[#6b4b3a]">
                  A short peer-style review ensures every question and answer feels classroom ready.
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
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#a6192e] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#5c0f1730] transition hover:bg-[#8f1326] disabled:cursor-not-allowed disabled:opacity-60"
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
          <div className="space-y-3 rounded-3xl bg-white p-6 shadow-xl shadow-rose-100/70 ring-1 ring-rose-100">
            <h2 className="text-sm font-semibold text-[#5c0f17]">
              Live updates
            </h2>

            {statusMessage && (
              <div className="rounded-xl border border-[#a6192e]/30 bg-[#a6192e]/5 px-3 py-2 text-xs text-[#5c0f17]">
                {isGenerating ? (
                  <p>
                    {statusMessage} This usually takes about a minute while we
                    read through the chapter and draft your activities.
                  </p>
                ) : (
                  <p>{statusMessage}</p>
                )}
              </div>
            )}

            {errorMessage && (
              <div className="rounded-xl border border-amber-400/80 bg-amber-50 px-3 py-2 text-xs text-[#5c0f17]">
                <p className="font-semibold">We hit a snag</p>
                <p className="mt-1 text-[0.7rem] leading-snug">{errorMessage}</p>
                <ul className="mt-2 list-disc pl-4 text-[0.7rem] text-[#6b4b3a]">
                  <li>Double-check your internet connection.</li>
                  <li>Try selecting the chapter again.</li>
                  <li>Reach out to your teaching assistant if it persists.</li>
                </ul>
              </div>
            )}

            {!statusMessage && !errorMessage && (
              <p className="text-xs text-[#6b4b3a]">
                Once you click <span className="font-semibold">Generate</span>,
                we&apos;ll keep you informed here—no tech jargon, just friendly
                updates.
              </p>
            )}
          </div>
        </section>

        {/* Problem set viewer */}
        <section className="space-y-4 rounded-3xl bg-white p-6 shadow-xl shadow-rose-100/70 ring-1 ring-rose-100">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-lg font-semibold text-[#5c0f17]">
              Your personalised practice set
            </h2>
            {problemSet && (
              <span className="rounded-full bg-[#f0e7dc] px-3 py-1 text-xs text-[#5c0f17]">
                {problemSet.num_problems ??
                  problemSet.problem_set?.length ??
                  0}{" "}
                {problemSet.num_problems === 1 ? "question" : "questions"}
              </span>
            )}
          </div>

          {!problemSet && (
            <p className="text-sm text-[#6b4b3a]">
              Once you generate a set, every question, hint, and solution will
              appear here ready for you to review or share with classmates.
            </p>
          )}

          {problemSet && (
            <div className="space-y-5 text-sm">
              {/* Simple summary */}
              <div className="rounded-2xl bg-[#f9f4ec] p-4 text-xs text-[#6b4b3a] ring-1 ring-rose-100">
                <p>
                  <span className="font-semibold text-[#5c0f17]">
                    Chapter:
                  </span>{" "}
                  {problemSet.doc_id}
                </p>
                {problemSet.analysis?.topics && (
                  <p className="mt-1">
                    <span className="font-semibold text-[#5c0f17]">
                      What this set covers:
                    </span>{" "}
                    {problemSet.analysis.topics.join(", ")}
                  </p>
                )}
              </div>

              {/* Problems list */}
              <div className="space-y-4">
                {(problemSet.problem_set || []).map(
                  (item: any, index: number) => {
                    const problem = item.problem ?? item;
                    const solution = item.solution;
                    const quality = item.quality;

                    return (
                      <details
                        key={index}
                        className="group rounded-2xl bg-[#fdfbf7] p-4 ring-1 ring-rose-100 open:shadow-lg open:shadow-rose-100/60"
                      >
                        <summary className="flex cursor-pointer list-none items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-wide text-[#8b1b26]/80">
                              Problem {index + 1}
                            </p>
                            <p className="mt-1 text-base font-medium text-[#2c1b14]">
                              {problem.statement || "Untitled problem"}
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2 text-[0.7rem] text-[#5c0f17]">
                              {problem.topic && (
                                <span className="rounded-full bg-[#f1e4d6] px-2 py-0.5">
                                  Topic · {problem.topic}
                                </span>
                              )}
                              {problem.difficulty && (
                                <span className="rounded-full bg-[#f1e4d6] px-2 py-0.5 capitalize">
                                  Difficulty · {problem.difficulty}
                                </span>
                              )}
                            </div>
                          </div>
                          <span className="mt-2 text-xs text-[#8b1b26]/70 group-open:rotate-90 transition-transform">
                            ▶
                          </span>
                        </summary>

                        <div className="mt-3 space-y-3 border-t border-rose-100 pt-3 text-xs leading-relaxed text-[#3e2b22]">
                          {problem.given && problem.given.length > 0 && (
                            <div>
                              <p className="font-semibold text-[#5c0f17]">
                                Given
                              </p>
                              <ul className="mt-1 list-disc pl-4">
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
                              <p className="font-semibold text-[#5c0f17]">
                                You&apos;re asked to find
                              </p>
                              <ul className="mt-1 list-disc pl-4">
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
                              <p className="font-semibold text-[#5c0f17]">
                                Solution walkthrough
                              </p>
                              <div className="markdown-card mt-2 rounded-xl bg-white p-4 ring-1 ring-rose-100">
                                <div className="markdown-body">
                                  <ReactMarkdown
                                    remarkPlugins={[remarkGfm, remarkMath]}
                                    rehypePlugins={[rehypeKatex]}
                                    components={markdownComponents}
                                  >
                                    {normalizeSolutionMarkdown(solution)}
                                  </ReactMarkdown>
                                </div>
                              </div>
                            </div>
                          )}

                          {quality && (
                            <div className="rounded-lg bg-[#f9f4ec] p-3 ring-1 ring-rose-100">
                              <p className="text-[0.75rem] font-semibold text-[#5c0f17]">
                                Quick review notes
                              </p>
                              <p className="mt-1 text-[0.75rem] text-[#3e2b22]">
                                Overall impression:{" "}
                                <span className="font-semibold capitalize text-[#5c0f17]">
                                  {quality.overall_quality ?? "unknown"}
                                </span>
                              </p>
                              {quality.issues && quality.issues.length > 0 && (
                                <div className="mt-1">
                                  <p className="text-[0.75rem] font-medium text-[#5c0f17]">
                                    Items to refine
                                  </p>
                                  <ul className="mt-1 list-disc pl-4 text-[0.75rem] text-[#3e2b22]">
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
                                    <p className="text-[0.75rem] font-medium text-[#5c0f17]">
                                      Suggestions from the reviewer
                                    </p>
                                    <ul className="mt-1 list-disc pl-4 text-[0.75rem] text-[#3e2b22]">
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
