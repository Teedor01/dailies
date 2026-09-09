"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, FileText, CheckCircle2, Database, Plus } from "lucide-react";
import { api } from "@/lib/api";
import type { Overview, InvestigationSummary } from "@/lib/types";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { PipelineTimeline } from "@/components/PipelineTimeline";

export default function OverviewPage() {
  const router = useRouter();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await api.overview();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load overview");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [load]);

  const handleNewInvestigation = async () => {
    setStarting(true);
    try {
      const { investigation_id } = await api.startInvestigation("orbital_ash");
      router.push(`/investigations/${investigation_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start investigation");
      setStarting(false);
    }
  };

  if (error) {
    return (
      <div className="p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}. Is the API running at{" "}
          <code className="font-mono">
            {process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}
          </code>
          ?
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="p-8 text-sm text-zinc-400">Loading...</div>;
  }

  const mostRecentRunning = data.investigations
    .filter((i) => i.status === "running")
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
  const mostRecent = mostRecentRunning ?? data.investigations
    .slice()
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];

  const recent: InvestigationSummary[] = data.investigations
    .slice()
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 5);

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Overview</h1>
          <p className="text-sm text-zinc-500">Across all investigations</p>
        </div>
        <button
          onClick={handleNewInvestigation}
          disabled={starting}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Plus size={16} />
          {starting ? "Starting..." : "New Investigation"}
        </button>
      </div>

      <div className="mb-6 grid grid-cols-4 gap-4">
        <StatCard label="Investigations" value={data.investigation_count} icon={Search} />
        <StatCard label="Running" value={data.running_count} icon={Database} />
        <StatCard label="Briefs Ready" value={data.brief_count} icon={FileText} />
        <StatCard label="Evidence Entries" value={data.total_evidence_entries} icon={CheckCircle2} />
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 rounded-xl border border-zinc-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-900">Recent Investigations</h2>
            <a href="/investigations" className="text-xs font-medium text-brand-600 hover:underline">
              View all
            </a>
          </div>
          {recent.length === 0 ? (
            <p className="py-8 text-center text-sm text-zinc-400">
              No investigations yet, start one to see it here.
            </p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                  <th className="py-2 font-medium">Title</th>
                  <th className="py-2 font-medium">Anomalies</th>
                  <th className="py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((inv) => (
                  <tr
                    key={inv.id}
                    onClick={() => router.push(`/investigations/${inv.id}`)}
                    className="cursor-pointer border-b border-zinc-100 last:border-0 hover:bg-zinc-50"
                  >
                    <td className="py-2.5 font-mono text-xs text-zinc-700">{inv.title_id}</td>
                    <td className="py-2.5 text-zinc-600">{inv.anomalies.length}</td>
                    <td className="py-2.5">
                      <StatusBadge status={inv.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-900">Investigation Pipeline</h2>
            {mostRecentRunning && (
              <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                Live
              </span>
            )}
          </div>
          {mostRecent ? (
            <>
              <p className="mb-3 font-mono text-xs text-zinc-500">{mostRecent.title_id}</p>
              <PipelineTimeline steps={mostRecent.steps} />
              <a
                href={`/investigations/${mostRecent.id}`}
                className="mt-1 block text-xs font-medium text-brand-600 hover:underline"
              >
                View full timeline &rarr;
              </a>
            </>
          ) : (
            <p className="py-8 text-center text-sm text-zinc-400">No pipeline running yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
