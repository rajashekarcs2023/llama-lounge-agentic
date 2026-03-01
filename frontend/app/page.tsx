"use client";

import { useState } from "react";
import {
  Search,
  Plus,
  Code2,
  BookOpen,
  Loader2,
  CheckCircle2,
  ChevronRight,
  Copy,
  Check,
  Zap,
  Globe,
  Brain,
  FileCode,
} from "lucide-react";

interface Source {
  site: string;
  pages: number;
  sections: string[];
}

interface ValidationEntry {
  attempt: number;
  valid: boolean;
  error: string;
}

interface GenerateResult {
  code: string;
  pages_used: string[];
  task: string;
  validation: ValidationEntry[];
}

type Phase = "idle" | "navigating" | "fetching" | "generating" | "validating" | "done";

const API = "http://localhost:8000";

export default function Home() {
  const [sources, setSources] = useState<Source[]>([]);
  const [urlInput, setUrlInput] = useState("");
  const [taskInput, setTaskInput] = useState("");
  const [indexing, setIndexing] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  const addSource = async () => {
    if (!urlInput.trim()) return;
    setIndexing(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/index`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: urlInput.trim() }),
      });
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setSources((prev) => {
          const exists = prev.find((s) => s.site === data.site);
          if (exists) return prev;
          return [
            ...prev,
            { site: data.site, pages: data.pages_indexed, sections: [] },
          ];
        });
        setUrlInput("");
      }
    } catch {
      setError("Failed to connect to backend. Is the API running?");
    }
    setIndexing(false);
  };

  const generate = async () => {
    if (!taskInput.trim()) return;
    setError("");
    setResult(null);
    setPhase("navigating");

    try {
      // Simulate phase transitions while waiting for the long-running API call
      const phaseTimer = (ms: number, next: Phase) =>
        new Promise<void>((r) => setTimeout(() => { setPhase(next); r(); }, ms));

      const apiCall = fetch(`${API}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: taskInput.trim() }),
      });

      // Progress through phases while waiting
      await phaseTimer(8000, "fetching");
      await phaseTimer(5000, "generating");
      await phaseTimer(15000, "validating");

      const res = await apiCall;
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        setPhase("idle");
      } else {
        setResult(data);
        setPhase("done");
      }
    } catch {
      setError("Failed to generate. Is the backend running on port 8000?");
      setPhase("idle");
    }
  };

  const copyCode = () => {
    if (result?.code) {
      navigator.clipboard.writeText(result.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const phaseLabels: Record<Phase, string> = {
    idle: "",
    navigating: "Navigator Agent is reasoning across all doc sites...",
    fetching: "Fetching selected documentation pages...",
    generating: "Code Crew is analyzing docs & writing code...",
    validating: "Validating code in Daytona sandbox...",
    done: "Code generated and validated!",
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-[#09090b]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-lg font-semibold tracking-tight">DocAgent</h1>
            <span className="text-xs text-zinc-500 border border-zinc-800 rounded-full px-2 py-0.5">
              v1.0
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs text-zinc-500">
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-yellow-500" />
              CrewAI + Composio
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Hero */}
        <div className="mb-10">
          <h2 className="text-3xl font-bold tracking-tight mb-2">
            The developer that reads{" "}
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              ALL
            </span>{" "}
            the docs.
          </h2>
          <p className="text-zinc-400 text-sm max-w-xl">
            Index documentation from any site. Describe what you want to build.
            DocAgent navigates across all your sources and generates
            production-ready code.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel: Sources + Task */}
          <div className="lg:col-span-1 space-y-6">
            {/* Add Source */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-medium">Documentation Sources</h3>
              </div>

              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && addSource()}
                  placeholder="https://docs.example.com"
                  className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm placeholder:text-zinc-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all"
                />
                <button
                  onClick={addSource}
                  disabled={indexing}
                  className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-zinc-700 disabled:text-zinc-400 text-white text-sm font-medium px-3 py-2 rounded-lg transition-colors flex items-center gap-1"
                >
                  {indexing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Quick add buttons */}
              <div className="flex flex-wrap gap-1.5 mb-4">
                {[
                  { label: "Composio", url: "https://docs.composio.dev" },
                  { label: "CrewAI", url: "https://docs.crewai.com" },
                  { label: "Skyfire", url: "https://docs.skyfire.xyz" },
                ].map((s) => (
                  <button
                    key={s.url}
                    onClick={() => {
                      setUrlInput(s.url);
                    }}
                    className="text-xs bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-md px-2 py-1 transition-colors"
                  >
                    + {s.label}
                  </button>
                ))}
              </div>

              {/* Source list */}
              <div className="space-y-2">
                {sources.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic">
                    No sources indexed yet. Add a documentation URL above.
                  </p>
                ) : (
                  sources.map((s) => (
                    <div
                      key={s.site}
                      className="flex items-center justify-between bg-zinc-800/50 rounded-lg px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-500" />
                        <span className="text-xs text-zinc-300 truncate max-w-[180px]">
                          {s.site.replace("https://", "")}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-500">
                          {s.pages} pages
                        </span>
                        <a
                          href={`${API}/api/pages`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-cyan-500 hover:text-cyan-400 transition-colors"
                        >
                          View Index
                        </a>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Task Input */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Search className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-medium">Describe Your Task</h3>
              </div>

              <textarea
                value={taskInput}
                onChange={(e) => setTaskInput(e.target.value)}
                placeholder="e.g. Build a CrewAI agent that uses Composio to send Gmail emails with authentication setup"
                rows={4}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm placeholder:text-zinc-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all resize-none"
              />

              <button
                onClick={generate}
                disabled={phase !== "idle" && phase !== "done"}
                className="w-full mt-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-zinc-700 disabled:to-zinc-700 disabled:text-zinc-400 text-white text-sm font-medium py-2.5 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {phase !== "idle" && phase !== "done" ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Code2 className="w-4 h-4" />
                    Generate Code
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Panel: Output */}
          <div className="lg:col-span-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 h-full min-h-[500px] flex flex-col">
              {/* Output header */}
              <div className="flex items-center justify-between border-b border-zinc-800 px-5 py-3">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-sm font-medium">Output</h3>
                </div>
                {result?.code && (
                  <button
                    onClick={copyCode}
                    className="text-xs text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-green-500" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        Copy code
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Pipeline status */}
              {phase !== "idle" && (
                <div className="px-5 py-3 border-b border-zinc-800">
                  <div className="flex items-center gap-6">
                    {(["navigating", "fetching", "generating", "validating", "done"] as Phase[]).map(
                      (p, i) => {
                        const isActive =
                          ["navigating", "fetching", "generating", "validating", "done"].indexOf(phase) >= i;
                        const isCurrent = phase === p;
                        return (
                          <div key={p} className="flex items-center gap-2">
                            {i > 0 && (
                              <ChevronRight
                                className={`w-3 h-3 ${isActive ? "text-cyan-400" : "text-zinc-700"}`}
                              />
                            )}
                            <div
                              className={`flex items-center gap-1.5 text-xs ${
                                isCurrent
                                  ? "text-cyan-400 font-medium"
                                  : isActive
                                    ? "text-zinc-300"
                                    : "text-zinc-600"
                              }`}
                            >
                              {isCurrent && phase !== "done" ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : isActive ? (
                                <CheckCircle2 className="w-3 h-3 text-green-500" />
                              ) : (
                                <div className="w-3 h-3 rounded-full border border-zinc-700" />
                              )}
                              {p === "navigating"
                                ? "Navigate"
                                : p === "fetching"
                                  ? "Fetch"
                                  : p === "generating"
                                    ? "Generate"
                                    : p === "validating"
                                      ? "Validate"
                                      : "Done"}
                            </div>
                          </div>
                        );
                      }
                    )}
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">
                    {phaseLabels[phase]}
                  </p>
                </div>
              )}

              {/* Pages used */}
              {result?.pages_used && result.pages_used.length > 0 && (
                <div className="px-5 py-3 border-b border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-2">
                    <BookOpen className="w-3 h-3 inline mr-1" />
                    Pages referenced ({result.pages_used.length}):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.pages_used.map((url) => (
                      <a
                        key={url}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-zinc-800 text-zinc-400 hover:text-cyan-400 rounded px-2 py-0.5 truncate max-w-[250px] transition-colors"
                      >
                        {url
                          .replace("https://docs.composio.dev/", "composio/")
                          .replace("https://docs.crewai.com/en/", "crewai/")
                          .replace("https://docs.skyfire.xyz/", "skyfire/")
                          .replace(".md", "")}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Validation result */}
              {result?.validation && result.validation.length > 0 && (
                <div className="px-5 py-3 border-b border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-2">
                    <CheckCircle2 className="w-3 h-3 inline mr-1" />
                    Validation ({result.validation.length} attempt{result.validation.length > 1 ? "s" : ""}):
                  </p>
                  <div className="space-y-1">
                    {result.validation.map((v) => (
                      <div key={v.attempt} className="flex items-center gap-2 text-xs">
                        {v.valid ? (
                          <CheckCircle2 className="w-3 h-3 text-green-500 shrink-0" />
                        ) : (
                          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500 shrink-0" />
                        )}
                        <span className={v.valid ? "text-green-400" : "text-red-400"}>
                          Attempt {v.attempt}: {v.valid ? "Passed" : v.error.slice(0, 80)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Code output */}
              <div className="flex-1 p-5 overflow-auto">
                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
                    <p className="text-sm text-red-400">{error}</p>
                  </div>
                )}

                {result?.code ? (
                  <pre className="bg-zinc-950 rounded-lg p-4 overflow-x-auto border border-zinc-800">
                    <code className="text-sm text-zinc-300 font-mono whitespace-pre">
                      {result.code}
                    </code>
                  </pre>
                ) : phase === "idle" ? (
                  <div className="h-full flex flex-col items-center justify-center text-center">
                    <div className="w-16 h-16 rounded-2xl bg-zinc-800/50 flex items-center justify-center mb-4">
                      <Code2 className="w-8 h-8 text-zinc-600" />
                    </div>
                    <p className="text-sm text-zinc-500 mb-1">
                      No code generated yet
                    </p>
                    <p className="text-xs text-zinc-600 max-w-sm">
                      Add documentation sources, describe your task, and
                      DocAgent will navigate the docs and generate working code.
                    </p>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <Loader2 className="w-8 h-8 text-cyan-500 animate-spin mx-auto mb-3" />
                      <p className="text-sm text-zinc-400">
                        {phaseLabels[phase]}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
