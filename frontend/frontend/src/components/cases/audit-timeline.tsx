"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getCaseAuditLogs, type AuditLogEvent } from "@/lib/api";

type Props = {
  caseId: string;
};

function formatEventLabel(eventType: string) {
  switch (eventType) {
    case "CASE_CREATED":
      return "Case Created";
    case "CASE_VIEWED":
      return "Case Viewed";
    case "CASES_LISTED":
      return "Cases Listed";
    case "CASE_NOT_FOUND":
      return "Case Not Found";
    case "TOOL_RUN_STARTED":
      return "Tool Run Started";
    case "TOOL_RUN_COMPLETED":
      return "Tool Run Completed";
    case "TOOL_RUN_FAILED":
      return "Tool Run Failed";
    case "AI_REVIEW_COMPLETED":
      return "AI Review Completed";
    case "AI_REVIEW_FAILED":
      return "AI Review Failed";
    default:
      return eventType
        .toLowerCase()
        .replaceAll("_", " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

function eventStyles(eventType: string) {
  if (eventType.includes("FAILED")) {
    return "border-red-900 bg-red-950/10";
  }
  if (eventType.includes("COMPLETED")) {
    return "border-emerald-900 bg-emerald-950/10";
  }
  if (eventType.includes("STARTED")) {
    return "border-amber-900 bg-amber-950/10";
  }
  if (eventType.includes("CREATED")) {
    return "border-blue-900 bg-blue-950/10";
  }
  return "border-slate-800 bg-slate-950";
}

function eventBadgeStyles(eventType: string) {
  if (eventType.includes("FAILED")) {
    return "border-red-800 bg-red-950/20 text-red-300";
  }
  if (eventType.includes("COMPLETED")) {
    return "border-emerald-800 bg-emerald-950/20 text-emerald-300";
  }
  if (eventType.includes("STARTED")) {
    return "border-amber-800 bg-amber-950/20 text-amber-300";
  }
  if (eventType.includes("CREATED")) {
    return "border-blue-800 bg-blue-950/20 text-blue-300";
  }
  return "border-slate-700 bg-slate-900 text-slate-300";
}

function readStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function readString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function readNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString();
}

function formatMetadataLabel(key: string) {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function MetadataChip({ value }: { value: string }) {
  return (
    <span className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
      {value}
    </span>
  );
}

function SummaryStat({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-sm text-slate-100">{value}</p>
    </div>
  );
}

function RenderStructuredMeta({ event }: { event: AuditLogEvent }) {
  const meta = event.meta;
  if (!meta || Object.keys(meta).length === 0) return null;

  const toolNames = readStringArray(meta.tool_names);
  const failedTools = readStringArray(meta.failed_tools);
  const requestedCount = readNumber(meta.requested_count);
  const resultCount = readNumber(meta.result_count);

  const decision = readString(meta.decision);
  const confidence =
    typeof meta.confidence === "number" ? String(meta.confidence) : null;
  const retryCount =
    typeof meta.retry_count === "number" ? String(meta.retry_count) : null;
  const modelProvider = readString(meta.model_provider);
  const modelName = readString(meta.model_name);
  const errorCategory = readString(meta.error_category);
  const errors = readStringArray(meta.errors);

  const remainingMeta = { ...meta };
  delete remainingMeta.tool_names;
  delete remainingMeta.failed_tools;
  delete remainingMeta.requested_count;
  delete remainingMeta.result_count;
  delete remainingMeta.statuses;
  delete remainingMeta.decision;
  delete remainingMeta.confidence;
  delete remainingMeta.retry_count;
  delete remainingMeta.model_provider;
  delete remainingMeta.model_name;
  delete remainingMeta.error_category;
  delete remainingMeta.errors;

  const hasRemainingMeta = Object.keys(remainingMeta).length > 0;

  return (
    <div className="mt-4 space-y-4">
      {(decision || confidence || retryCount || modelProvider || modelName || errorCategory) && (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {decision && <SummaryStat label="Decision" value={decision} />}
          {confidence && <SummaryStat label="Confidence" value={confidence} />}
          {retryCount && <SummaryStat label="Retry Count" value={retryCount} />}
          {modelProvider && (
            <SummaryStat label="Model Provider" value={modelProvider} />
          )}
          {modelName && <SummaryStat label="Model Name" value={modelName} />}
          {errorCategory && (
            <SummaryStat label="Error Category" value={errorCategory} />
          )}
          {requestedCount !== null && (
            <SummaryStat
              label="Requested Tools"
              value={String(requestedCount)}
            />
          )}
          {resultCount !== null && (
            <SummaryStat label="Result Count" value={String(resultCount)} />
          )}
        </div>
      )}

      {toolNames.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Tools
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {toolNames.map((toolName) => (
              <MetadataChip key={toolName} value={toolName} />
            ))}
          </div>
        </div>
      )}

      {failedTools.length > 0 && (
        <div className="rounded-xl border border-red-900 bg-red-950/10 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-red-400">
            Failed Tools
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {failedTools.map((toolName) => (
              <span
                key={toolName}
                className="rounded-md border border-red-800 px-2 py-1 text-xs text-red-300"
              >
                {toolName}
              </span>
            ))}
          </div>
        </div>
      )}

      {errors.length > 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Errors
          </p>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {"statuses" in meta && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Tool Statuses
          </p>
          <pre className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs text-slate-300">
            {JSON.stringify(meta.statuses, null, 2)}
          </pre>
        </div>
      )}

      {hasRemainingMeta && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
            Additional Metadata
          </p>
          <pre className="mt-3 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 text-xs text-slate-300">
            {JSON.stringify(remainingMeta, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function AuditTimeline({ caseId }: Props) {
  const [events, setEvents] = useState<AuditLogEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAuditLogs = useCallback(
    async (isRefresh = false) => {
      try {
        if (isRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        setError(null);

        const json = await getCaseAuditLogs(caseId);
        setEvents(Array.isArray(json) ? json : []);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load audit timeline."
        );
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [caseId]
  );

  useEffect(() => {
    void loadAuditLogs(false);
  }, [loadAuditLogs]);

  const groupedCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const event of events) {
      counts.set(event.event_type, (counts.get(event.event_type) || 0) + 1);
    }
    return counts;
  }, [events]);

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Audit Timeline</h2>
          <p className="mt-1 text-sm text-slate-400">
            Operational history and audit trail for this case.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-400">
            Total events:{" "}
            <span className="font-medium text-slate-200">{events.length}</span>
          </div>

          <button
            onClick={() => void loadAuditLogs(true)}
            disabled={loading || refreshing}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {refreshing ? "Refreshing..." : "Refresh Timeline"}
          </button>
        </div>
      </div>

      {!loading && !error && events.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {Array.from(groupedCounts.entries()).map(([eventType, count]) => (
            <span
              key={eventType}
              className={`rounded-md border px-2 py-1 text-xs ${eventBadgeStyles(
                eventType
              )}`}
            >
              {formatEventLabel(eventType)} · {count}
            </span>
          ))}
        </div>
      )}

      {loading && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          Loading audit events...
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/20 p-4">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}

      {!loading && !error && events.length === 0 && (
        <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          No audit events found for this case yet.
        </div>
      )}

      {events.length > 0 && (
        <div className="mt-4 space-y-4">
          {events.map((event) => (
            <div
              key={event.id}
              className={`rounded-xl border p-4 ${eventStyles(event.event_type)}`}
            >
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-slate-100">
                      {formatEventLabel(event.event_type)}
                    </p>
                    <span
                      className={`rounded-md border px-2 py-1 text-[11px] ${eventBadgeStyles(
                        event.event_type
                      )}`}
                    >
                      {event.subject || "event"}
                    </span>
                  </div>

                  <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                    Event Time
                  </p>
                  <p className="mt-1 text-sm text-slate-300">
                    {formatDateTime(event.created_at)}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[420px]">
                  <SummaryStat
                    label="Actor"
                    value={event.actor_type || "N/A"}
                  />
                  <SummaryStat
                    label="Latency"
                    value={
                      event.latency_ms !== null
                        ? `${event.latency_ms} ms`
                        : "N/A"
                    }
                  />
                  <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                      Event ID
                    </p>
                    <p className="mt-2 font-mono text-xs text-slate-100 break-all">
                      {event.id}
                    </p>
                  </div>
                </div>
              </div>

              <RenderStructuredMeta event={event} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}