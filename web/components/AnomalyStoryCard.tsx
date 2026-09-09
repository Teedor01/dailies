import type { Anomaly, EvidenceEntry } from "@/lib/types";
import { formatCompactCount, formatPercentFromFraction, formatBaselineDelta, roundLooseDecimalsInText } from "@/lib/format";

function headline(a: Anomaly): { title: string; observed: string; expected: string; delta: string } {
  const isCompletion = a.anomaly_type.includes("completion");
  const baseline = isCompletion ? a.baseline_range?.p50_completion_pct : a.baseline_range?.p50_views_per_hour;
  const direction = a.anomaly_type.includes("negative") ? "dropped" : a.anomaly_type.includes("positive") ? "surged" : "changed";
  const metricLabel = isCompletion ? "completion" : "viewership";

  if (baseline == null) {
    return { title: `${a.region} ${metricLabel} ${direction}`, observed: String(a.observed_value), expected: "unknown", delta: "" };
  }
  if (isCompletion) {
    return {
      title: `${a.region} completion ${direction}`,
      observed: formatPercentFromFraction(a.observed_value),
      expected: `${formatPercentFromFraction(baseline)} expected`,
      delta: formatBaselineDelta(a.observed_value, baseline, true),
    };
  }
  return {
    title: `${a.region} viewership ${direction}`,
    observed: `${formatCompactCount(a.observed_value)} views`,
    expected: `${formatCompactCount(baseline)} expected`,
    delta: formatBaselineDelta(a.observed_value, baseline, false),
  };
}


function investigationBlurb(anomalyId: string, evidenceLog: EvidenceEntry[]): string | null {
  const summary = evidenceLog.find(
    (e) => e.anomaly_id === anomalyId && e.step === "INVESTIGATE" && e.entry_type === "observed_fact" && e.sql == null
  );
  if (!summary) return null;
  const cleaned = roundLooseDecimalsInText(summary.claim);
  return cleaned.length > 220 ? cleaned.slice(0, 217).trimEnd() + "..." : cleaned;
}

export function AnomalyStoryCard({
  anomaly,
  evidenceLog,
  onViewInvestigation,
}: {
  anomaly: Anomaly;
  evidenceLog: EvidenceEntry[];
  onViewInvestigation: () => void;
}) {
  const { title, observed, expected, delta } = headline(anomaly);
  const blurb = investigationBlurb(anomaly.anomaly_id, evidenceLog);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5">
      <h3 className="text-base font-bold text-zinc-900">{title}</h3>
      <div className="mt-2 flex items-baseline gap-3">
        <span className="text-2xl font-bold text-zinc-900">{observed}</span>
        <span className="text-sm text-zinc-500">{expected}</span>
      </div>
      {delta && <p className="mt-0.5 text-xs font-medium text-zinc-500">{delta}</p>}
      <p className="mt-1 text-xs text-zinc-400">
        Hours {anomaly.window_start_hour},{anomaly.window_end_hour}
      </p>

      {blurb && <p className="mt-3 text-sm text-zinc-700">{blurb}</p>}

      <button
        onClick={onViewInvestigation}
        className="mt-4 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
      >
        View investigation &rarr;
      </button>
    </div>
  );
}
