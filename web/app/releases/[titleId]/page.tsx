"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/api";
import type { InvestigationSummary, Anomaly } from "@/lib/types";
import { MovieHeader } from "@/components/MovieHeader";
import { deriveReleaseHealth, releaseHealthStyle, latestInvestigationFor } from "@/lib/releaseHealth";


function describeAnomaly(a: Anomaly): string {
  const isCompletion = a.anomaly_type.includes("completion");
  const baseline = isCompletion ? a.baseline_range?.p50_completion_pct : a.baseline_range?.p50_views_per_hour;
  const metricLabel = isCompletion ? "completion" : "viewing volume";
  const direction = a.anomaly_type.includes("negative") ? "dropped" : a.anomaly_type.includes("positive") ? "rose" : "changed";

  if (baseline == null) {
    return `${a.region} ${metricLabel} ${direction} to ${a.observed_value} during hours ${a.window_start_hour}-${a.window_end_hour} after release.`;
  }
  if (isCompletion) {
    return `${a.region} completion ${direction} from ${(baseline * 100).toFixed(0)}% baseline to ${(a.observed_value * 100).toFixed(0)}%.`;
  }
  const multiplier = (a.observed_value / baseline).toFixed(1);
  return `${a.region} viewing volume is ${multiplier}x expected baseline.`;
}

export default function ReleasePage({ params }: { params: { titleId: string } }) {
  const { titleId } = params;
  const router = useRouter();
  const [investigations, setInvestigations] = useState<InvestigationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    try {
      const all = await api.listInvestigations();
      setInvestigations(all);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load release");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000); 
    return () => clearInterval(interval);
  }, [load]);

  const startInvestigation = async () => {
    setStarting(true);
    try {
      const { investigation_id } = await api.startInvestigation(titleId);
      router.push(`/investigations/${investigation_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start investigation");
      setStarting(false);
    }
  };

  if (error) {
    return (
      <div className="p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      </div>
    );
  }
  if (!investigations) {
    return <div className="p-8 text-sm text-zinc-400">Loading release...</div>;
  }

  const latest = latestInvestigationFor(titleId, investigations);
  const health = deriveReleaseHealth(latest);
  const style = releaseHealthStyle(health);
  const anomalies = latest?.anomalies ?? [];

  return (
    <div className="p-8">
      <Link href="/" className="mb-3 flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-700">
        <ChevronLeft size={16} />
        Your Releases
      </Link>

      <MovieHeader title={latest?.title ?? null} />

      <div className="mb-6 flex items-center justify-between rounded-xl border border-zinc-200 bg-white p-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">Release Health</div>
          <span className={`mt-1 inline-block rounded-md px-2 py-1 text-sm font-bold tracking-wide ${style.bg} ${style.text}`}>
            {style.label}
          </span>
        </div>
        {!latest && (
          <button
            onClick={startInvestigation}
            disabled={starting}
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {starting ? "Starting..." : "Check release now"}
          </button>
        )}
      </div>

      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">What&rsquo;s happening?</h2>

      {!latest ? (
        <p className="rounded-xl border border-zinc-200 bg-white p-6 text-sm text-zinc-500">
          No investigation has been run for this release yet.
        </p>
      ) : anomalies.length === 0 ? (
        <p className="rounded-xl border border-zinc-200 bg-white p-6 text-sm text-zinc-500">
          No anomalies detected. This release is tracking within baseline.
        </p>
      ) : (
        <div className="space-y-3">
          {anomalies.map((a) => (
            <div key={a.anomaly_id} className="rounded-xl border border-zinc-200 bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm text-zinc-800">{describeAnomaly(a)}</p>
                  <p className="mt-1 text-xs text-zinc-500">
                    Hours {a.window_start_hour}-{a.window_end_hour} after release
                  </p>
                </div>
                <span className="shrink-0 rounded-md bg-red-50 px-2 py-1 text-xs font-bold tracking-wide text-red-700">
                  ATTENTION
                </span>
              </div>
              <Link
                href={`/investigations/${latest.id}?anomaly=${a.anomaly_id}`}
                className="mt-3 inline-block rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
              >
                {latest.status === "running" ? "View investigation in progress" : "Investigate anomaly"}
              </Link>
            </div>
          ))}
        </div>
      )}

      {latest?.brief && (
        <div className="mt-6">
          <Link
            href={`/investigations/${latest.id}`}
            className="inline-block rounded-lg border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
          >
            {latest.title?.title_name ?? titleId}: First 72 Hours Release Brief &rarr;
          </Link>
        </div>
      )}
    </div>
  );
}
