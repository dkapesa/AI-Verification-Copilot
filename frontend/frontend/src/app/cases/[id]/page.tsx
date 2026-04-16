import Link from "next/link";
import AIReviewPanel from "@/components/cases/ai-review-panel";
import AuditTimeline from "@/components/cases/audit-timeline";
import HumanOverridePanel from "@/components/cases/human-override-panel";
import ToolResultsPanel from "@/components/cases/tool-results-panel";
import { getCase } from "@/lib/api";
import { formatDateTime, formatLabel } from "@/lib/format";
import { getCaseStatusBadgeClasses } from "@/lib/status";

type PageProps = {
  params: Promise<{ id: string }>;
};

type JsonObject = Record<string, unknown>;

function isPlainObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPrimitiveValue(value: unknown) {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null
  );
}

function isEmptyPlainObject(value: unknown) {
  return isPlainObject(value) && Object.keys(value).length === 0;
}

function isEmptyArray(value: unknown) {
  return Array.isArray(value) && value.length === 0;
}

function isPlaceholderKey(key: string) {
  return /^additionalprop\d+$/i.test(key);
}

function isMeaningfulValue(value: unknown) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string" && value.trim() === "") return false;
  if (isEmptyPlainObject(value)) return false;
  if (isEmptyArray(value)) return false;
  return true;
}

function formatPrimitiveValue(key: string, value: unknown) {
  if (value === null) return "N/A";

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    if (key === "session_duration") {
      return `${value} seconds`;
    }

    return String(value);
  }

  return String(value);
}

function JsonBlock({ value }: { value: unknown }) {
  return (
    <pre className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs leading-6 text-slate-300">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function MetadataItem({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p
        className={`mt-2 text-sm text-slate-100 ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function StructuredField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p
        className={`mt-2 text-sm text-slate-100 ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function StructuredDataSection({
  title,
  value,
}: {
  title: string;
  value: unknown;
}) {
  if (!isPlainObject(value)) {
    return (
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <div className="mb-4">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
            Structured Signals
          </p>
          <h2 className="mt-1 text-lg font-semibold">{title}</h2>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          No structured data available for this section.
        </div>
      </section>
    );
  }

  const filteredEntries = Object.entries(value).filter(([key, entryValue]) => {
    if (isPlaceholderKey(key) && !isMeaningfulValue(entryValue)) {
      return false;
    }

    return isMeaningfulValue(entryValue);
  });

  const primitiveEntries = filteredEntries.filter(([, entryValue]) =>
    isPrimitiveValue(entryValue)
  );

  const complexEntries = filteredEntries.filter(
    ([, entryValue]) => !isPrimitiveValue(entryValue)
  );

  const hasMeaningfulData =
    primitiveEntries.length > 0 || complexEntries.length > 0;

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-4">
        <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
          Structured Signals
        </p>
        <h2 className="mt-1 text-lg font-semibold">{title}</h2>
      </div>

      {!hasMeaningfulData && (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-400">
          No structured data available for this section.
        </div>
      )}

      {primitiveEntries.length > 0 && (
        <div className="grid gap-3 md:grid-cols-2">
          {primitiveEntries.map(([key, entryValue]) => (
            <StructuredField
              key={key}
              label={formatLabel(key)}
              value={formatPrimitiveValue(key, entryValue)}
              mono={key.includes("id") || key.includes("ip")}
            />
          ))}
        </div>
      )}

      {complexEntries.length > 0 && (
        <div className="mt-4 space-y-4">
          {complexEntries.map(([key, entryValue]) => (
            <div key={key}>
              <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
                {formatLabel(key)}
              </p>
              <JsonBlock value={entryValue} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default async function CaseDetailPage({ params }: PageProps) {
  const { id } = await params;
  const data = await getCase(id);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-4">
          <Link
            href="/cases"
            className="inline-flex items-center rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800"
          >
            ← Back to Queue
          </Link>
        </div>

        <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-400">
                Case Detail
              </p>

              <div className="mt-2 flex flex-col gap-3 lg:flex-row lg:items-center">
                <h1
                  className="truncate font-mono text-xl font-semibold sm:text-2xl"
                  title={data.id}
                >
                  {data.id}
                </h1>

                <span
                  className={`inline-flex w-fit rounded-md border px-2.5 py-1 text-xs font-medium ${getCaseStatusBadgeClasses(
                    data.status
                  )}`}
                >
                  {data.status}
                </span>
              </div>

              <p className="mt-3 max-w-3xl text-sm text-slate-400">
                Analyst review view for persisted verification case data,
                deterministic tool outputs, AI decisioning, and audit history.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:min-w-[360px] xl:max-w-[420px]">
              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                  Created
                </p>
                <p className="mt-2 text-sm text-slate-100">
                  {formatDateTime(data.created_at)}
                </p>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
                <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">
                  Updated
                </p>
                <p className="mt-2 text-sm text-slate-100">
                  {formatDateTime(data.updated_at)}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <MetadataItem label="Email" value={data.email} />
            <MetadataItem label="User ID" value={data.user_id} mono />
            <MetadataItem label="Case Status" value={data.status} />
            <MetadataItem label="Case ID" value={data.id} mono />
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-2">
          <StructuredDataSection title="Device Info" value={data.device_info} />
          <StructuredDataSection
            title="Document Check Result"
            value={data.document_check_result}
          />
          <div className="xl:col-span-2">
            <StructuredDataSection
              title="Behaviour Summary"
              value={data.behaviour_summary}
            />
          </div>
        </div>

        <div className="mt-6">
          <ToolResultsPanel caseId={data.id} />
        </div>

        <div className="mt-6">
          <AIReviewPanel caseId={data.id} />
        </div>

        <div className="mt-6">
          <HumanOverridePanel caseId={data.id} />
        </div>

        <div className="mt-6">
          <AuditTimeline caseId={data.id} />
        </div>
      </div>
    </main>
  );
}