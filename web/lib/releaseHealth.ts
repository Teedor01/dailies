import type { InvestigationSummary } from "./types";

export type ReleaseHealth = "ATTENTION" | "INVESTIGATING" | "MONITORING" | "ERROR";

const HEALTH_STYLE: Record<ReleaseHealth, { bg: string; text: string; label: string }> = {
  ATTENTION: { bg: "bg-red-50", text: "text-red-700", label: "ATTENTION" },
  INVESTIGATING: { bg: "bg-amber-50", text: "text-amber-700", label: "INVESTIGATING" },
  MONITORING: { bg: "bg-emerald-50", text: "text-emerald-700", label: "MONITORING" },
  ERROR: { bg: "bg-zinc-100", text: "text-zinc-600", label: "ERROR" },
};


export function latestInvestigationFor(
  titleId: string,
  investigations: InvestigationSummary[]
): InvestigationSummary | null {
  const matches = investigations.filter((inv) => inv.title_id === titleId);
  if (matches.length === 0) return null;
  return matches.reduce((latest, inv) => (inv.created_at > latest.created_at ? inv : latest));
}


export function deriveReleaseHealth(investigation: InvestigationSummary | null): ReleaseHealth {
  if (!investigation) return "MONITORING";
  if (investigation.status === "error") return "ERROR";
  if (investigation.anomalies.length === 0) return "MONITORING";
  if (investigation.status === "running") return "INVESTIGATING";
  return "ATTENTION";
}

export function releaseHealthStyle(health: ReleaseHealth) {
  return HEALTH_STYLE[health];
}
