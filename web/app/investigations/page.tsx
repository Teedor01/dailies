"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Plus, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import type { InvestigationSummary } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

export default function InvestigationsPage() {
  const router = useRouter();
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [filter, setFilter] = useState<"all" | "running" | "complete" | "error">("all");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await api.listInvestigations();
      setInvestigations(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load investigations");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, [load]);

  const handleNew = async () => {
    setStarting(true);
    try {
      const { investigation_id } = await api.startInvestigation("orbital_ash");
      router.push(`/investigations/${investigation_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start investigation");
      setStarting(false);
    }
  };

  const filtered =
    filter === "all" ? investigations : investigations.filter((i) => i.status === filter);

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Investigations</h1>
          <p className="text-sm text-zinc-500">All investigations across titles</p>
        </div>
        <button
          onClick={handleNew}
          disabled={starting}
          className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Plus size={16} />
          {starting ? "Starting..." : "New Investigation"}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mb-4 flex gap-2">
        {(["all", "running", "complete", "error"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium capitalize ${
              filter === f ? "bg-zinc-900 text-white" : "bg-white text-zinc-600 border border-zinc-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="rounded-xl border border-zinc-200 bg-white">
        {filtered.length === 0 ? (
          <p className="py-12 text-center text-sm text-zinc-400">No investigations match this filter.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Anomalies</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Updated</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((inv) => (
                <tr
                  key={inv.id}
                  onClick={() => router.push(`/investigations/${inv.id}`)}
                  className="cursor-pointer border-b border-zinc-100 last:border-0 hover:bg-zinc-50"
                >
                  <td className="px-4 py-3 font-mono text-xs text-zinc-700">{inv.title_id}</td>
                  <td className="px-4 py-3 text-zinc-600">
                    {inv.anomalies.map((a) => a.region).join(", ") || "-"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={inv.status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-zinc-400">
                    {new Date(inv.updated_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <ChevronRight size={16} className="inline text-zinc-300" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
