import type { EvidenceType } from "@/lib/types";

const STYLES: Record<EvidenceType, { bg: string; text: string; label: string }> = {
  observed_fact: { bg: "bg-blue-50", text: "text-blue-700", label: "observed_fact" },
  correlation: { bg: "bg-violet-50", text: "text-violet-700", label: "correlation" },
  hypothesis: { bg: "bg-amber-50", text: "text-amber-700", label: "hypothesis" },
  verified_finding: { bg: "bg-green-50", text: "text-green-700", label: "verified_finding" },
  rejected_hypothesis: { bg: "bg-red-50", text: "text-red-700", label: "rejected_hypothesis" },
  inconclusive_finding: { bg: "bg-orange-50", text: "text-orange-700", label: "inconclusive_finding" },
  notable_pattern: { bg: "bg-sky-50", text: "text-sky-700", label: "notable_pattern" },
  query_error: { bg: "bg-zinc-100", text: "text-zinc-500", label: "query_error" },
};

export function EvidenceTypeBadge({ type }: { type: EvidenceType }) {
  const style = STYLES[type] ?? STYLES.observed_fact;
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}
