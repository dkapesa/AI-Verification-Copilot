"use client";

import { useMemo, useState } from "react";
import { API_BASE_URL } from "@/lib/config";

type Props = {
  caseId: string;
};

type OverrideDecision = "APPROVE" | "ESCALATE" | "REJECT";

function decisionStyles(decision: OverrideDecision) {
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

function decisionHelpText(decision: OverrideDecision) {
  switch (decision) {
    case "APPROVE":
      return "Approve the case despite prior automated uncertainty or after confirming risk is acceptable.";
    case "ESCALATE":
      return "Escalate the case for further analyst review, additional checks, or specialist handling.";
    case "REJECT":
      return "Reject the case based on manual review, policy concerns, or confirmed fraud indicators.";
    default:
      return "Select a reviewer decision.";
  }
}

function StatCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "warning";
}) {
  const toneClasses =
    tone === "warning"
      ? "border-amber-900 bg-amber-950/10"
      : "border-slate-800 bg-slate-950";

  return (
    <div className={`rounded-xl border p-4 ${toneClasses}`}>
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-sm text-slate-200">{value}</p>
    </div>
  );
}

export default function HumanOverridePanel({ caseId }: Props) {
  const [decision, setDecision] = useState<OverrideDecision>("ESCALATE");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const trimmedNote = note.trim();

  const noteCount = useMemo(() => note.length, [note]);

  async function submitOverride() {
    try {
      setLoading(true);
      setError(null);
      setMessage(null);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/cases/${caseId}/human-override`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            decision,
            note: trimmedNote,
          }),
        }
      );

      const text = await response.text();

      if (!response.ok) {
        throw new Error(`API error ${response.status}: ${text}`);
      }

      setMessage(
        `Human override submitted with decision ${decision}. The current backend endpoint is still a placeholder/stub, but the human-in-the-loop workflow is now clearly represented in the UI.`
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to submit human override."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold">Human Override</h2>
          <p className="mt-1 text-sm text-slate-400">
            Allow a human reviewer to override or confirm the automated outcome.
          </p>
        </div>

        <span className="inline-flex w-fit rounded-md border border-amber-800 bg-amber-950/20 px-2.5 py-1 text-xs font-medium text-amber-300">
          Placeholder Workflow
        </span>
      </div>

      <div className="mt-4 grid gap-3 xl:grid-cols-3">
        <StatCard
          label="Current Endpoint State"
          value="Connected to placeholder backend route"
          tone="warning"
        />
        <StatCard
          label="Persistence Status"
          value="Not yet fully persisted end-to-end"
          tone="warning"
        />
        <StatCard
          label="Review Intent"
          value="Expose the human-in-the-loop path in the analyst console"
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
          <label className="mb-2 block text-sm font-medium text-slate-200">
            Reviewer Decision
          </label>

          <select
            value={decision}
            onChange={(e) => {
              setDecision(e.target.value as OverrideDecision);
              setMessage(null);
              setError(null);
            }}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none"
          >
            <option value="APPROVE">APPROVE</option>
            <option value="ESCALATE">ESCALATE</option>
            <option value="REJECT">REJECT</option>
          </select>

          <p className="mt-3 text-sm text-slate-400">
            {decisionHelpText(decision)}
          </p>
        </div>

        <div
          className={`rounded-2xl border p-4 ${decisionStyles(decision)}`}
        >
          <p className="text-[11px] uppercase tracking-[0.18em] opacity-80">
            Selected Override
          </p>
          <p className="mt-2 text-xl font-semibold">{decision}</p>
          <p className="mt-3 text-sm opacity-90">
            This represents the reviewer’s manual decision path, even before the
            full override persistence and audit workflow are finalized.
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-800 bg-slate-950 p-4">
        <div className="flex items-center justify-between gap-3">
          <label className="block text-sm font-medium text-slate-200">
            Reviewer Note
          </label>
          <span className="text-xs text-slate-500">{noteCount} characters</span>
        </div>

        <textarea
          value={note}
          onChange={(e) => {
            setNote(e.target.value);
            setMessage(null);
            setError(null);
          }}
          rows={5}
          placeholder="Add reviewer context, rationale, escalation notes, or supporting observations..."
          className="mt-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500"
        />

        <p className="mt-3 text-sm text-slate-500">
          Suggested content: why the override is justified, what signals mattered
          most, and what should happen next operationally.
        </p>
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-sm text-slate-500">
          Case ID: <span className="font-mono text-slate-300">{caseId}</span>
        </div>

        <button
          onClick={submitOverride}
          disabled={loading}
          className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Submitting..." : "Submit Human Override"}
        </button>
      </div>

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-900 bg-emerald-950/20 p-4">
          <p className="text-sm text-emerald-300">{message}</p>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/20 p-4">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}
    </section>
  );
}