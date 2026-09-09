import type { InvestigationSummary, Anomaly, EvidenceEntry } from "./types";
import { formatPercentFromFraction, stripStructuredBlocks, firstSentence } from "./format";

function anomalyPhrase(a: Anomaly): string {
  const isCompletion = a.anomaly_type.includes("completion");
  const isPositive = a.anomaly_type.includes("positive");
  if (isPositive) return `an unexpected viewing-volume surge in ${a.region}`;
  if (isCompletion) return `a sharp completion decline concentrated in ${a.region}`;
  return `an unusual pattern in ${a.region}`;
}


function severityScore(a: Anomaly): number {
  if (a.anomaly_type.includes("negative")) return 2;
  if (a.anomaly_type.includes("positive")) return 1;
  return 0;
}


function groundedLine(anomaly: Anomaly, investigation: InvestigationSummary): string {
  const verdict = investigation.evidence_log.find(
    (e) => e.entry_type === "verified_finding" && e.anomaly_id === anomaly.anomaly_id
  );
  if (verdict) return firstSentence(stripStructuredBlocks(verdict.claim));

  const summary = investigation.evidence_log.find(
    (e: EvidenceEntry) => e.anomaly_id === anomaly.anomaly_id && e.step === "INVESTIGATE" && e.entry_type === "observed_fact" && e.sql == null
  );
  if (summary) return firstSentence(stripStructuredBlocks(summary.claim));

  return `${anomaly.region} is still under investigation.`;
}


export function buildHeroNarrative(investigation: InvestigationSummary): { overview: string } {
  const movie = investigation.title?.title_name ?? investigation.title_id;
  const perf = investigation.title?.overall_performance;
  const anomalies = investigation.anomalies;

  let performanceClause = "is being tracked for release performance";
  if (perf) {
    const delta = perf.delta_pct;
    const qualifier = Math.abs(delta) < 0.02 ? "close to" : delta < 0 ? "below" : "above";
    performanceClause = `is performing ${qualifier} its expected completion rate overall (${formatPercentFromFraction(
      perf.avg_completion_pct
    )} vs. ${formatPercentFromFraction(perf.baseline_completion_pct)} baseline)`;
  }

  if (anomalies.length === 0) {
    return { overview: `${movie} ${performanceClause}, and no release anomalies have been detected.` };
  }
  return {
    overview: `${movie} ${performanceClause}, but Dailies detected ${anomalies.length} important release anomal${
      anomalies.length === 1 ? "y" : "ies"
    } that need attention.`,
  };
}


export function buildReleaseTakeaway(investigation: InvestigationSummary): {
  paragraph: string;
  priority: { region: string; text: string } | null;
  alsoMonitor: { region: string; text: string }[];
} {
  const movie = investigation.title?.title_name ?? investigation.title_id;
  const anomalies = investigation.anomalies;

  let paragraph: string;
  if (anomalies.length === 0) {
    paragraph = `${movie} is tracking within expected performance, with no release anomalies identified so far.`;
  } else {
    const list = anomalies.map(anomalyPhrase).join(", and ");
    paragraph = `${movie} is broadly tracking near its expected completion rate, but Dailies identified ${
      anomalies.length
    } area${anomalies.length === 1 ? "" : "s"} worth investigating further: ${list}.`;
  }


  const verifiedAnomalies = anomalies.filter((a) =>
    investigation.evidence_log.some((e) => e.entry_type === "verified_finding" && e.anomaly_id === a.anomaly_id)
  );

  let priority: { region: string; text: string } | null = null;
  let alsoMonitor: { region: string; text: string }[] = [];

  if (verifiedAnomalies.length > 0) {
    const ranked = [...verifiedAnomalies].sort((a, b) => severityScore(b) - severityScore(a));
    const top = ranked[0];
    const direction = top.anomaly_type.includes("negative") ? "decline" : top.anomaly_type.includes("positive") ? "increase" : "anomaly";
    priority = {
      region: top.region,
      text: `${groundedLine(top, investigation)} This is the strongest supported explanation from the available evidence for the ${direction} and should be reviewed by the release team.`,
    };
    alsoMonitor = anomalies
      .filter((a) => a.anomaly_id !== top.anomaly_id)
      .map((a) => ({ region: a.region, text: groundedLine(a, investigation) }));
  }

  return { paragraph, priority, alsoMonitor };
}
