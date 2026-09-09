"use client";

import { useEffect, useState, useCallback } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import type { EvidenceEntry, EvidenceType } from "@/lib/types";
import { EvidenceTypeBadge } from "@/components/EvidenceTypeBadge";
import { EvidenceDetailPanel } from "@/components/EvidenceDetailPanel";

const TYPES: (EvidenceType | "all")[] = [
  "all",
  "observed_fact",
  "correlation",
  "hypothesis",
  "verified_finding",
  "rejected_hypothesis",
  "query_error",
];
const STEPS = ["all", "OBSERVE", "INVESTIGATE", "HYPOTHESIZE", "VERIFY", "BRIEF"];

export default function EvidenceExplorerPage() {
  const [entries, setEntries] = useState<EvidenceEntry[]>([]);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [stepFilter, setStepFilter] = useState<string>("all");
  const [selected, setSelected] = useState<EvidenceEntry | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const results = await api.searchEvidence({
        q: query || undefined,
        entry_type: typeFilter !== "all" ? typeFilter : undefined,
        step: stepFilter !== "all" ? stepFilter : undefined,
      });
      setEntries(results);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load evidence");
    }
  }, [query, typeFilter, stepFilter]);

  useEffect(() => {
    const t = setTimeout(load, 200); 
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div className="p-8">
      <h1 className="mb-1 text-2xl font-bold text-zinc-900">Evidence Explorer</h1>
      <p className="mb-6 text-sm text-zinc-500">Search and explore all evidence</p>

      <div className="mb-4 flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search evidence..."
            className="w-full rounded-lg border border-zinc-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-400"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
        >
          {TYPES.map((t) => (
            <option key={t} value={t}>{t === "all" ? "All Types" : t}</option>
          ))}
        </select>
        <select
          value={stepFilter}
          onChange={(e) => setStepFilter(e.target.value)}
          className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
        >
          {STEPS.map((s) => (
            <option key={s} value={s}>{s === "all" ? "All Steps" : s}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-zinc-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                <th className="px-3 py-2 font-medium">ID</th>
                <th className="px-3 py-2 font-medium">Type</th>
                <th className="px-3 py-2 font-medium">Step</th>
                <th className="px-3 py-2 font-medium">Claim</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-sm text-zinc-400">
                    No evidence matches this filter.
                  </td>
                </tr>
              ) : (
                entries.map((entry) => (
                  <tr
                    key={`${entry.investigation_id}-${entry.id}`}
                    onClick={() => setSelected(entry)}
                    className={`cursor-pointer border-b border-zinc-100 last:border-0 hover:bg-zinc-50 ${
                      selected?.id === entry.id ? "bg-brand-50" : ""
                    }`}
                  >
                    <td className="px-3 py-2 font-mono text-xs text-zinc-700">{entry.id}</td>
                    <td className="px-3 py-2">
                      <EvidenceTypeBadge type={entry.entry_type} />
                    </td>
                    <td className="px-3 py-2 text-xs text-zinc-500">{entry.step}</td>
                    <td className="max-w-xs truncate px-3 py-2 text-xs text-zinc-600">{entry.claim}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div>
          {selected ? (
            <EvidenceDetailPanel entry={selected} />
          ) : (
            <p className="p-8 text-center text-sm text-zinc-400">Select an evidence entry to inspect it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
