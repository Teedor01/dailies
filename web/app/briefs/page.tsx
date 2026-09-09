"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { FileText, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import type { BriefSummary } from "@/lib/types";

export default function BriefsPage() {
  const [briefs, setBriefs] = useState<BriefSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await api.listBriefs();
      setBriefs(result.slice().sort((a, b) => b.created_at.localeCompare(a.created_at)));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load briefs");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  return (
    <div className="p-8">
      <h1 className="mb-1 text-2xl font-bold text-zinc-900">Briefs</h1>
      <p className="mb-6 text-sm text-zinc-500">AI-generated briefs with verified evidence</p>

      {error && (
        <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {briefs.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-white py-16 text-center text-sm text-zinc-400">
          No briefs yet... start an investigation and let it run through to BRIEF.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {briefs.map((b) => {
            const clean = b.validation_problems.length === 0;
            return (
              <Link
                key={b.investigation_id}
                href={`/investigations/${b.investigation_id}`}
                className="rounded-xl border border-zinc-200 bg-white p-4 hover:border-brand-300"
              >
                <div className="mb-2 flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <FileText size={16} />
                  </div>
                  <div>
                    <div className="font-mono text-xs text-zinc-500">{b.title_id}</div>
                    <div className="text-xs text-zinc-400">
                      {new Date(b.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <p className="mb-3 line-clamp-2 text-sm text-zinc-700">{b.brief.summary}</p>
                <div
                  className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ${
                    clean ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {clean ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                  {clean ? "Verified \u2014 All citations valid" : `${b.validation_problems.length} issue(s)`}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
