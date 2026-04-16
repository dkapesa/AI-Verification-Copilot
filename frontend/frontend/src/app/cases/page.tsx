"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getCases } from "@/lib/api";
import { formatCaseId, formatDateTime } from "@/lib/format";
import { getCaseStatusBadgeClasses } from "@/lib/status";
import type { CaseListResponse, CaseSummary } from "@/types/case";

function countStatuses(items: CaseSummary[]) {
  return items.reduce(
    (acc, item) => {
      const normalized = item.status.toUpperCase();

      if (normalized === "PENDING") acc.pending += 1;
      else if (normalized === "APPROVED") acc.approved += 1;
      else if (normalized === "ESCALATED" || normalized === "ESCALATE")
        acc.escalated += 1;
      else if (normalized === "REJECTED" || normalized === "REJECT")
        acc.rejected += 1;
      else acc.other += 1;

      return acc;
    },
    {
      pending: 0,
      approved: 0,
      escalated: 0,
      rejected: 0,
      other: 0,
    }
  );
}

function SummaryChip({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "pending" | "approved" | "escalated" | "rejected";
}) {
  const toneClasses =
    tone === "approved"
      ? "border-emerald-800 bg-emerald-950/20 text-emerald-300"
      : tone === "escalated"
      ? "border-amber-800 bg-amber-950/20 text-amber-300"
      : tone === "rejected"
      ? "border-red-800 bg-red-950/20 text-red-300"
      : tone === "pending"
      ? "border-slate-700 bg-slate-950 text-slate-300"
      : "border-slate-700 bg-slate-950 text-slate-300";

  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${toneClasses}`}>
      <div className="uppercase tracking-[0.18em] opacity-80">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  );
}

export default function CasesPage() {
  const [data, setData] = useState<CaseListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [offset, setOffset] = useState(0);

  const loadCases = useCallback(
    async (isRefresh = false) => {
      try {
        if (isRefresh) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        setError(null);

        const json = await getCases(limit, offset);
        setData(json);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load cases.";
        setError(message);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [limit, offset]
  );

  useEffect(() => {
    void loadCases(false);
  }, [loadCases]);

  const filteredItems = useMemo(() => {
    if (!data) return [];

    const normalized = query.trim().toLowerCase();
    if (!normalized) return data.items;

    return data.items.filter((item: CaseSummary) => {
      return (
        item.id.toLowerCase().includes(normalized) ||
        item.email.toLowerCase().includes(normalized) ||
        item.user_id.toLowerCase().includes(normalized) ||
        item.status.toLowerCase().includes(normalized)
      );
    });
  }, [data, query]);

  const statusCounts = useMemo(
    () => countStatuses(filteredItems),
    [filteredItems]
  );

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / limit)) : 1;
  const canGoPrev = offset > 0;
  const canGoNext = data ? offset + limit < data.total : false;

  const pageStart = data && data.total > 0 ? offset + 1 : 0;
  const pageEnd = data ? Math.min(offset + limit, data.total) : 0;

  function goPrev() {
    if (!canGoPrev) return;
    setOffset(Math.max(0, offset - limit));
  }

  function goNext() {
    if (!canGoNext) return;
    setOffset(offset + limit);
  }

  function handleLimitChange(value: number) {
    setLimit(value);
    setOffset(0);
  }

  async function handleRefresh() {
    await loadCases(true);
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-5 flex flex-col gap-2">
          <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">
            Operations Queue
          </p>

          <div className="flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Verification Cases</h1>
              <p className="mt-1 text-sm text-slate-400">
                Browse persisted verification cases from the backend API.
              </p>
            </div>

            <div className="text-xs text-slate-500">
              {data
                ? `Showing ${pageStart}-${pageEnd} of ${data.total} cases`
                : "Waiting for case data"}
            </div>
          </div>
        </div>

        <div className="mb-4 rounded-2xl border border-slate-800 bg-slate-900 p-4">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
              <div className="w-full xl:max-w-md">
                <label
                  htmlFor="case-search"
                  className="mb-2 block text-xs uppercase tracking-[0.18em] text-slate-400"
                >
                  Search Queue
                </label>
                <input
                  id="case-search"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Case ID, email, user ID, or status..."
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500"
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:w-auto">
                <button
                  onClick={handleRefresh}
                  disabled={loading || refreshing}
                  className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {refreshing ? "Refreshing..." : "Refresh"}
                </button>

                <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-400 sm:justify-start">
                  <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    Rows
                  </span>
                  <select
                    value={limit}
                    onChange={(e) => handleLimitChange(Number(e.target.value))}
                    className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100"
                  >
                    <option value={5}>5</option>
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-400">
                  <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
                    Matches
                  </span>
                  <span className="font-medium text-slate-200">
                    {filteredItems.length}
                  </span>
                </div>
              </div>
            </div>

            {!loading && !error && (
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
                <SummaryChip
                  label="Visible Cases"
                  value={filteredItems.length}
                  tone="default"
                />
                <SummaryChip
                  label="Pending"
                  value={statusCounts.pending}
                  tone="pending"
                />
                <SummaryChip
                  label="Approved"
                  value={statusCounts.approved}
                  tone="approved"
                />
                <SummaryChip
                  label="Escalated"
                  value={statusCounts.escalated}
                  tone="escalated"
                />
                <SummaryChip
                  label="Rejected"
                  value={statusCounts.rejected}
                  tone="rejected"
                />
              </div>
            )}
          </div>
        </div>

        {loading && (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 text-sm text-slate-300">
            Loading verification cases...
          </div>
        )}

        {error && (
          <div className="rounded-2xl border border-red-900 bg-slate-900 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-red-400">
              Cases Load Error
            </p>
            <h2 className="mt-2 text-xl font-semibold">
              Unable to load verification cases
            </h2>
            <p className="mt-4 text-sm text-slate-300">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
              <div className="max-h-[70vh] overflow-auto">
                <table className="min-w-[1120px] divide-y divide-slate-800 text-sm">
                  <thead className="sticky top-0 z-10 bg-slate-900/95 text-slate-400 backdrop-blur">
                    <tr>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Case ID
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Email
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        User ID
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Status
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Created
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Updated
                      </th>
                      <th className="px-3 py-3 text-left text-xs font-medium uppercase tracking-[0.16em]">
                        Action
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-800">
                    {filteredItems.map((item) => (
                      <tr
                        key={item.id}
                        className="group hover:bg-slate-800/40 transition-colors"
                      >
                        <td
                          className="px-3 py-3 font-mono text-xs text-slate-200"
                          title={item.id}
                        >
                          <div className="flex items-center gap-2">
                            <span>{formatCaseId(item.id)}</span>
                            <span className="hidden rounded border border-slate-700 px-1.5 py-0.5 text-[10px] text-slate-500 group-hover:inline-flex">
                              UUID
                            </span>
                          </div>
                        </td>

                        <td
                          className="max-w-[260px] truncate px-3 py-3 text-sm text-slate-200"
                          title={item.email}
                        >
                          {item.email}
                        </td>

                        <td
                          className="max-w-[220px] truncate px-3 py-3 font-mono text-xs text-slate-300"
                          title={item.user_id}
                        >
                          {item.user_id}
                        </td>

                        <td className="px-3 py-3">
                          <span
                            className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-medium ${getCaseStatusBadgeClasses(
                              item.status
                            )}`}
                          >
                            {item.status}
                          </span>
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 text-xs text-slate-300">
                          {formatDateTime(item.created_at)}
                        </td>

                        <td className="whitespace-nowrap px-3 py-3 text-xs text-slate-300">
                          {formatDateTime(item.updated_at)}
                        </td>

                        <td className="px-3 py-3">
                          <Link
                            href={`/cases/${item.id}`}
                            className="inline-flex rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-800 group-hover:border-slate-600"
                          >
                            Open Case
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {filteredItems.length === 0 && (
                <div className="px-4 py-8 text-sm text-slate-400">
                  No matching cases found.
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-sm text-slate-400">
                Page <span className="font-medium text-slate-200">{currentPage}</span>{" "}
                of <span className="font-medium text-slate-200">{totalPages}</span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={goPrev}
                  disabled={!canGoPrev}
                  className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>

                <button
                  onClick={goNext}
                  disabled={!canGoNext}
                  className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}