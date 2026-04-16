"use client";

import { useEffect, useMemo, useState } from "react";
import { APIError, getLatestAIReview, runCaseAIReview } from "@/lib/api";
import { formatNumericValue, formatToolName } from "@/lib/format";
import StatCard from "@/components/ui/stat-card";
import type { AIReviewResult } from "@/types/ai-review";

type Props = {
  caseId: string;
};

function decisionStyles(decision: string) {
  switch (decision) {
    case "APPROVE":
      return "border-emerald-800 bg-emerald-950/30 text-emerald-300";
    case "ESCALATE":
      return "border-amber-800 bg-amber-950/30 text-amber-300";
    case "REJECT":
      return "border-red-800 bg-red-950/30 text-red-300";
    default:
      return "border-slate-700 bg-slate-900 text-slate-200";
  }
}

function riskScoreStyles(score: number) {
  if (score >= 0.8) return "border-red-800 bg-red-950/20 text-red-300";
  if (score >= 0.4) return "border-amber-800 bg-amber-950/20 text-amber-300";
  return "border-emerald-800 bg-emerald-950/20 text-emerald-300";
}

function normalizeAIReview(raw: any): AIReviewResult {
  return {
    case_id: typeof raw.case_id === "string" ? raw.case_id : undefined,
    decision:
      typeof raw?.decision?.decision === "string"
        ? raw.decision.decision
        : "ESCALATE",
    confidence:
      typeof raw?.decision?.confidence === "number"
        ? raw.decision.confidence
        : 0,
    reasons: Array.isArray(raw?.decision?.reasons) ? raw.decision.reasons : [],
    recommended_next_steps: Array.isArray(raw?.decision?.recommended_next_steps)
      ? raw.decision.recommended_next_steps
      : [],
    aggregated_signals:
      raw.aggregated_signals && typeof raw.aggregated_signals === "object"
        ? {
            overall_risk_score:
              typeof raw.aggregated_signals.overall_risk_score === "number"
                ? raw.aggregated_signals.overall_risk_score
                : 0,
            high_risk_flags: Array.isArray(raw.aggregated_signals.high_risk_flags)
              ? raw.aggregated_signals.high_risk_flags
              : [],
            moderate_risk_flags: Array.isArray(
              raw.aggregated_signals.moderate_risk_flags
            )
              ? raw.aggregated_signals.moderate_risk_flags
              : [],
            low_risk_flags: Array.isArray(raw.aggregated_signals.low_risk_flags)
              ? raw.aggregated_signals.low_risk_flags
              : [],
            tool_summaries: Array.isArray(raw.aggregated_signals.tool_summaries)
              ? raw.aggregated_signals.tool_summaries
              : [],
            tools_failed: Array.isArray(raw.aggregated_signals.tools_failed)
              ? raw.aggregated_signals.tools_failed
              : [],
          }
        : undefined,
    reasoning_summary:
      typeof raw.reasoning_summary === "string" ? raw.reasoning_summary : null,
  };
}

function ListSection({
  title,
  items,
  emptyLabel = "None",
}: {
  title: string;
  items: string[];
  emptyLabel?: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
      {items.length > 0 ? (
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-400">{emptyLabel}</p>
      )}
    </div>
  );
}

export default function AIReviewPanel({ caseId }: Props) {
  const [loading, setLoading] = useState(false);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIReviewResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadLatestReview() {
      try {
        setLoadingLatest(true);
        setError(null);

        const raw = await getLatestAIReview(caseId);

        if (!cancelled) {
          setResult(normalizeAIReview(raw));
        }
      } catch (err) {
        if (err instanceof APIError && err.status === 404) {
          if (!cancelled) {
            setResult(null);
          }
          return;
        }

        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load latest AI review."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingLatest(false);
        }
      }
    }

    void loadLatestReview();

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  async function runReview() {
    try {
      setLoading(true);
      setError(null);

      const raw = await runCaseAIReview(caseId);
      setResult(normalizeAIReview(raw));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run AI review.");
    } finally {
      setLoading(false);
    }
  }

  const flagSummary = useMemo(() => {
    if (!result?.aggregated_signals) {
      return {
        high: 0,
        moderate: 0,
        low: 0,
        failedTools: 0,
      };
    }

    return {
      high: result.aggregated_signals.high_risk_flags.length,
      moderate: result.aggregated_signals.moderate_risk_flags.length,
      low: result.aggregated_signals.low_risk_flags.length,
      failedTools: result.aggregated_signals.tools_failed.length,
    };
  }, [result]);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold">AI Review</h2>
          <p className="mt-1 text-sm text-slate-400">
            Trigger AI-assisted fraud decisioning for this case.
          </p>
        </div>

        <button
          onClick={runReview}
          disabled={loading}
          className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Running..." : "Run AI Review"}
        </button>
      </div>

      {loadingLatest && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          Loading latest AI review...
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/20 p-4">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loadingLatest && !result && !error && !loading && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          No AI review run yet for this case.
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-4">
          <div
            className={`rounded-xl border p-4 ${decisionStyles(result.decision)}`}
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] opacity-80">
                  Decision
                </p>
                <h3 className="mt-1 text-2xl font-semibold">{result.decision}</h3>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[260px]">
                <StatCard
                  label="Confidence"
                  value={formatNumericValue(result.confidence, 2)}
                  className="border-current/20 bg-black/10"
                  labelClassName="opacity-80"
                  valueClassName="text-current"
                />

                {result.aggregated_signals && (
                  <StatCard
                    label="Risk Score"
                    value={formatNumericValue(
                      result.aggregated_signals.overall_risk_score,
                      2
                    )}
                    className="border-current/20 bg-black/10"
                    labelClassName="opacity-80"
                    valueClassName="text-current"
                  />
                )}
              </div>
            </div>
          </div>

          {result.aggregated_signals && (
            <>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <div
                  className={`rounded-xl border p-4 ${riskScoreStyles(
                    result.aggregated_signals.overall_risk_score
                  )}`}
                >
                  <p className="text-[11px] uppercase tracking-[0.18em] opacity-80">
                    Overall Risk Score
                  </p>
                  <p className="mt-2 text-2xl font-semibold">
                    {formatNumericValue(
                      result.aggregated_signals.overall_risk_score,
                      2
                    )}
                  </p>
                </div>

                <StatCard label="High Risk Flags" value={flagSummary.high} />
                <StatCard
                  label="Moderate Risk Flags"
                  value={flagSummary.moderate}
                />
                <StatCard label="Low Risk Flags" value={flagSummary.low} />
              </div>

              {flagSummary.failedTools > 0 && (
                <div className="rounded-xl border border-red-900 bg-red-950/10 p-4">
                  <p className="text-[11px] uppercase tracking-[0.18em] text-red-400">
                    Tools Failed During Review
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {result.aggregated_signals.tools_failed.map((toolName) => (
                      <span
                        key={toolName}
                        className="rounded-md border border-red-800 px-2 py-1 text-xs text-red-300"
                      >
                        {formatToolName(toolName)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          <div className="grid gap-4 xl:grid-cols-2">
            <ListSection
              title="Reasons"
              items={result.reasons}
              emptyLabel="No reasons returned."
            />
            <ListSection
              title="Recommended Next Steps"
              items={result.recommended_next_steps}
              emptyLabel="No recommended next steps returned."
            />
          </div>

          {result.aggregated_signals && (
            <div className="grid gap-4 xl:grid-cols-3">
              <ListSection
                title="High Risk Flags"
                items={result.aggregated_signals.high_risk_flags}
              />
              <ListSection
                title="Moderate Risk Flags"
                items={result.aggregated_signals.moderate_risk_flags}
              />
              <ListSection
                title="Low Risk Flags"
                items={result.aggregated_signals.low_risk_flags}
              />
            </div>
          )}

          {result.aggregated_signals && (
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <h3 className="text-sm font-semibold text-slate-200">
                Tool Summaries
              </h3>

              {result.aggregated_signals.tool_summaries.length > 0 ? (
                <div className="mt-3 space-y-3">
                  {result.aggregated_signals.tool_summaries.map((tool, index) => (
                    <div
                      key={`${tool.tool_name}-${index}`}
                      className="rounded-lg border border-slate-800 bg-slate-900 p-3"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0">
                          <p className="font-medium text-slate-200">
                            {formatToolName(tool.tool_name)}
                          </p>
                          <p className="mt-1 text-sm text-slate-400">
                            {tool.summary}
                          </p>
                        </div>

                        <div className="grid gap-2 sm:grid-cols-2 lg:min-w-[220px]">
                          <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
                            Score: {formatNumericValue(tool.score, 2)}
                          </div>
                          <div className="rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300">
                            Confidence: {formatNumericValue(tool.confidence, 2)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-400">
                  No tool summaries returned.
                </p>
              )}
            </div>
          )}

          {result.reasoning_summary && (
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <h3 className="text-sm font-semibold text-slate-200">
                Reasoning Summary
              </h3>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                {result.reasoning_summary}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}