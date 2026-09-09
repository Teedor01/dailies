import type { Anomaly } from "@/lib/types";
import { ReleaseFindingCard, type FindingGroup } from "./ReleaseFindingCard";

const STEPS = [
  { key: "OBSERVE", label: "OBSERVE" },
  { key: "INVESTIGATE", label: "INVESTIGATE" },
  { key: "HYPOTHESIZE", label: "HYPOTHESIZE" },
  { key: "VERIFY", label: "VERIFY" },
] as const;

function StepArrow() {
  return <div className="my-1 ml-4 h-4 w-px bg-zinc-200" />;
}

export function InvestigationNarrative({
  movieName,
  anomaly,
  totalAnomalyCount,
  findingGroups,
  onSelectEvidence,
}: {
  movieName: string;
  anomaly: Anomaly;
  totalAnomalyCount: number;
  findingGroups: FindingGroup[];
  onSelectEvidence: (id: string) => void;
}) {
  const direction = anomaly.anomaly_type.includes("negative") ? "decline" : anomaly.anomaly_type.includes("positive") ? "increase" : "change";
  const hypothesisCount = findingGroups.length;


  const stepText: Record<string, string> = {
    OBSERVE: `Dailies detected ${totalAnomalyCount} unusual pattern${totalAnomalyCount === 1 ? "" : "s"} during ${movieName}'s first 72 hours.`,
    INVESTIGATE: `It compared region, device, app version and playback behavior for the ${anomaly.region} ${direction}.`,
    HYPOTHESIZE:
      hypothesisCount > 0
        ? `It considered ${hypothesisCount} possible explanation${hypothesisCount === 1 ? "" : "s"} for the ${anomaly.region} ${direction}.`
        : `Hypothesis generation in progress...`,
    VERIFY: `ClickHouse data was queried to test ${hypothesisCount === 1 ? "that explanation" : "those explanations"}.`,
  };

  return (
    <div>
      {STEPS.map((step) => (
        <div key={step.key}>
          <div className="rounded-xl border border-zinc-200 bg-white p-4">
            <div className="text-xs font-bold tracking-wide text-brand-700">{step.label}</div>
            <p className="mt-1 text-sm text-zinc-700">{stepText[step.key]}</p>
          </div>
          <StepArrow />
        </div>
      ))}

      <div className="rounded-xl border-2 border-brand-200 bg-brand-50/40 p-4">
        <div className="mb-3 text-xs font-bold tracking-wide text-brand-700">FINDING</div>
        {findingGroups.length === 0 ? (
          <p className="text-sm text-zinc-500">Verification in progress...</p>
        ) : (
          <div className="space-y-3">
            {findingGroups.map((group) => (
              <ReleaseFindingCard
                key={group.hypothesis.id}
                group={group}
                onSelectEvidence={onSelectEvidence}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
