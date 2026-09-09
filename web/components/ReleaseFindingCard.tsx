import type { EvidenceEntry } from "@/lib/types";
import { VERDICT_LABEL, VERDICT_STYLE, EvidenceCount, MetricComparison } from "./FindingDisplay";
import { stripStructuredBlocks, roundLooseDecimalsInText } from "@/lib/format";


export interface FindingGroup {
  hypothesis: EvidenceEntry;
  verdict: EvidenceEntry | null;
}

export function groupFindings(evidenceLog: EvidenceEntry[]): FindingGroup[] {
  const hypotheses = evidenceLog.filter((e) => e.entry_type === "hypothesis");
  const verdictByHypothesis = new Map<string, EvidenceEntry>();
  for (const e of evidenceLog) {
    if (e.verifies_hypothesis) verdictByHypothesis.set(e.verifies_hypothesis, e);
  }
  return hypotheses.map((hypothesis) => ({
    hypothesis,
    verdict: verdictByHypothesis.get(hypothesis.id) ?? null,
  }));
}


export function ReleaseFindingCard({
  group,
  onSelectEvidence,
}: {
  group: FindingGroup;
  onSelectEvidence?: (evidenceId: string) => void;
}) {
  const { hypothesis, verdict } = group;
  const allEvidenceIds = Array.from(new Set([...hypothesis.supports, ...(verdict?.supports ?? [])]));

  const groundedLabel =
    verdict?.entry_type === "verified_finding"
      ? "Verified finding"
      : verdict?.entry_type === "rejected_hypothesis"
      ? "Contradicting evidence"
      : null;

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4">
      <div className="mb-3">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">Hypothesis</div>
        <p className="mt-0.5 text-sm italic text-zinc-600">{hypothesis.claim}</p>
      </div>

      <div className="mb-1 flex items-center gap-2">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">Status</div>
        {verdict ? (
          <span
            className={`rounded-md border px-2 py-0.5 text-[11px] font-bold tracking-wide ${
              VERDICT_STYLE[verdict.entry_type] ?? "bg-zinc-50 text-zinc-600 border-zinc-200"
            }`}
          >
            {VERDICT_LABEL[verdict.entry_type] ?? verdict.entry_type}
          </span>
        ) : (
          <span className="text-xs text-zinc-400">Pending...</span>
        )}
      </div>

      {groundedLabel && (
        <div className="mt-2">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-400">{groundedLabel}</div>
          {verdict?.key_metrics ? (
            <MetricComparison metrics={verdict.key_metrics} />
          ) : (
            <p className="mt-0.5 text-sm text-zinc-700">
              {roundLooseDecimalsInText(stripStructuredBlocks(verdict!.claim))}
            </p>
          )}
        </div>
      )}

      {verdict?.entry_type === "inconclusive_finding" && (
        <p className="mt-2 text-xs text-zinc-500">Dailies could not determine this from the available data.</p>
      )}

      {onSelectEvidence && <EvidenceCount ids={allEvidenceIds} onOpen={onSelectEvidence} />}
    </div>
  );
}
