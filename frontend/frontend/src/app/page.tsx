import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8">
          <p className="text-sm uppercase tracking-[0.2em] text-slate-400">
            AI Verification Copilot
          </p>

          <h1 className="mt-3 text-3xl font-semibold">
            Internal Fraud Review Dashboard
          </h1>

          <p className="mt-4 max-w-2xl text-sm text-slate-300">
            Browse verification cases, inspect structured fraud signals, and
            review AI-assisted decision outputs.
          </p>

          <div className="mt-6">
            <Link
              href="/cases"
              className="inline-flex rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700"
            >
              Open Case Queue
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}