"use client";

import { useEffect, useMemo, useState } from "react";
import {
  APIError,
  getCaseToolRuns,
  runCaseTools,
  type ToolResult,
} from "@/lib/api";
import {
  formatDateTime,
  formatNumericValue,
  formatToolName,
} from "@/lib/format";
import StatCard from "@/components/ui/stat-card";

type ToolResultWithDetails = ToolResult & {
  signals?: unknown;
  output?: unknown;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  latency_ms?: number | null;
};

type Props = {
  caseId: string;
};

function statusClasses(status: string) {
  switch (status) {
    case "SUCCESS":
      return "border-emerald-800 bg-emerald-950/20 text-emerald-300";
    case "FAILED":
      return "border-red-800 bg-red-950/20 text-red-300";
    case "RUNNING":
      return "border-amber-800 bg-amber-950/20 text-amber-300";
    default:
      return "border-slate-700 bg-slate-900 text-slate-300";
  }
}

function formatScore(value: number | null) {
  return formatNumericValue(value, 2);
}

function formatConfidence(value: number | null) {
  return formatNumericValue(value, 2);
}

function hasKeys(value: unknown) {
  return (
    typeof value === "object" &&
    value !== null &&
    Object.keys(value as Record<string, unknown>).length > 0
  );
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs leading-6 text-slate-300">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function ToolResultsPanel({ caseId }: Props) {
  const [results, setResults] = useState<ToolResultWithDetails[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>(
    {}
  );

  useEffect(() => {
    let cancelled = false;

    async function loadLatestToolRuns() {
      try {
        setLoadingLatest(true);
        setError(null);

        const raw = await getCaseToolRuns(caseId);

        if (!cancelled) {
          setResults(Array.isArray(raw.results) ? raw.results : []);
        }
      } catch (err) {
        if (err instanceof APIError && err.status === 404) {
          if (!cancelled) {
            setResults([]);
          }
          return;
        }

        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load latest tool results."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingLatest(false);
        }
      }
    }

    void loadLatestToolRuns();

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  async function runTools() {
    try {
      setLoading(true);
      setError(null);

      const raw = await runCaseTools(caseId);
      setResults(Array.isArray(raw.results) ? raw.results : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run tools.");
    } finally {
      setLoading(false);
    }
  }

  function toggleExpanded(toolName: string) {
    setExpandedTools((current) => ({
      ...current,
      [toolName]: !current[toolName],
    }));
  }

  const resultSummary = useMemo(() => {
    const successCount = results.filter(
      (tool) => tool.status === "SUCCESS"
    ).length;
    const failedCount = results.filter((tool) => tool.status === "FAILED").length;
    const runningCount = results.filter((tool) => tool.status === "RUNNING").length;

    return {
      total: results.length,
      successCount,
      failedCount,
      runningCount,
    };
  }, [results]);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Deterministic Tool Results</h2>
          <p className="mt-1 text-sm text-slate-400">
            Execute fraud analysis tools and inspect structured outputs.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          {results.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <span className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300">
                Total · {resultSummary.total}
              </span>
              <span className="rounded-md border border-emerald-800 bg-emerald-950/20 px-2 py-1 text-xs text-emerald-300">
                Success · {resultSummary.successCount}
              </span>
              {resultSummary.failedCount > 0 && (
                <span className="rounded-md border border-red-800 bg-red-950/20 px-2 py-1 text-xs text-red-300">
                  Failed · {resultSummary.failedCount}
                </span>
              )}
              {resultSummary.runningCount > 0 && (
                <span className="rounded-md border border-amber-800 bg-amber-950/20 px-2 py-1 text-xs text-amber-300">
                  Running · {resultSummary.runningCount}
                </span>
              )}
            </div>
          )}

          <button
            onClick={runTools}
            disabled={loading}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Running..." : "Run Tools"}
          </button>
        </div>
      </div>

      {loadingLatest && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          Loading latest tool results...
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/20 p-4">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loadingLatest && !error && results.length === 0 && !loading && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
          <p className="text-sm text-slate-300">
            No tool results loaded yet for this case.
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Run the deterministic tools to generate and persist analyst-facing
            fraud signals for this case.
          </p>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-4 grid gap-4 xl:grid-cols-2">
          {results.map((tool) => {
            const isExpanded = expandedTools[tool.tool_name] ?? false;
            const hasDetailSections =
              hasKeys(tool.signals) ||
              hasKeys(tool.output) ||
              Boolean(tool.error_message) ||
              Boolean(tool.started_at) ||
              Boolean(tool.completed_at) ||
              tool.latency_ms !== undefined;

            return (
              <div
                key={tool.tool_name}
                className="rounded-xl border border-slate-800 bg-slate-950 p-4"
              >
                <div className="flex flex-col gap-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="truncate font-semibold text-slate-100">
                        {formatToolName(tool.tool_name)}
                      </h3>
                      <p className="mt-2 text-sm text-slate-400">
                        {tool.summary || "No summary returned."}
                      </p>
                    </div>

                    <span
                      className={`inline-flex shrink-0 rounded-md border px-2 py-1 text-xs font-medium ${statusClasses(
                        tool.status
                      )}`}
                    >
                      {tool.status}
                    </span>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <StatCard label="Score" value={formatScore(tool.score)} />
                    <StatCard
                      label="Confidence"
                      value={formatConfidence(tool.confidence)}
                    />
                  </div>

                  {hasDetailSections && (
                    <div className="flex items-center justify-between gap-3 border-t border-slate-800 pt-3">
                      <div className="text-xs text-slate-500">
                        Additional persisted detail available
                      </div>

                      <button
                        type="button"
                        onClick={() => toggleExpanded(tool.tool_name)}
                        className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-900"
                      >
                        {isExpanded ? "Hide Details" : "Show Details"}
                      </button>
                    </div>
                  )}

                  {isExpanded && hasDetailSections && (
                    <div className="space-y-4 border-t border-slate-800 pt-4">
                      <div className="grid gap-3 md:grid-cols-3">
                        <StatCard
                          label="Started"
                          value={formatDateTime(tool.started_at)}
                        />
                        <StatCard
                          label="Completed"
                          value={formatDateTime(tool.completed_at)}
                        />
                        <StatCard
                          label="Latency"
                          value={
                            tool.latency_ms !== null &&
                            tool.latency_ms !== undefined
                              ? `${tool.latency_ms} ms`
                              : "N/A"
                          }
                        />
                      </div>

                      {tool.error_message && (
                        <div className="rounded-lg border border-red-900 bg-red-950/10 p-4">
                          <p className="text-[11px] uppercase tracking-[0.18em] text-red-400">
                            Error Message
                          </p>
                          <p className="mt-2 text-sm text-red-300">
                            {tool.error_message}
                          </p>
                        </div>
                      )}

                      {hasKeys(tool.signals) && (
                        <div>
                          <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
                            Signals
                          </p>
                          <JsonBlock value={tool.signals} />
                        </div>
                      )}

                      {hasKeys(tool.output) && (
                        <div>
                          <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
                            Raw Output
                          </p>
                          <JsonBlock value={tool.output} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}