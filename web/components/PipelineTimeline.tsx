import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { StepName, StepState } from "@/lib/types";

const STEP_ORDER: StepName[] = ["OBSERVE", "INVESTIGATE", "HYPOTHESIZE", "VERIFY", "BRIEF"];

const STEP_LABELS: Record<StepName, { title: string; description: string }> = {
  OBSERVE: { title: "OBSERVE", description: "Deterministic anomaly scan" },
  INVESTIGATE: { title: "INVESTIGATE", description: "Agent exploring anomaly shape" },
  HYPOTHESIZE: { title: "HYPOTHESIZE", description: "Generating candidate hypotheses" },
  VERIFY: { title: "VERIFY", description: "Testing hypotheses with targeted queries" },
  BRIEF: { title: "BRIEF", description: "Synthesizing verified findings" },
};

function stepDetail(step: StepName, state: StepState): string | null {
  const payload = state.data;
  if (!payload) return null;
  switch (step) {
    case "OBSERVE":
      return typeof payload.anomaly_count === "number"
        ? `${payload.anomaly_count} anomal${payload.anomaly_count === 1 ? "y" : "ies"} detected`
        : null;
    case "INVESTIGATE":
      return Array.isArray(payload.evidence_ids)
        ? `${payload.evidence_ids.length} evidence entries logged`
        : null;
    case "HYPOTHESIZE":
      return Array.isArray(payload.hypotheses)
        ? `${payload.hypotheses.length} hypotheses generated`
        : null;
    case "VERIFY":
      return payload.hypothesis_id && payload.verdict
        ? `${payload.hypothesis_id}: ${payload.verdict}`
        : null;
    case "BRIEF":
      if (Array.isArray(payload.problems)) {
        return payload.problems.length > 0
          ? `${payload.problems.length} validation issue(s)`
          : "All citations valid";
      }
      return null;
    default:
      return null;
  }
}

function StepIcon({ status }: { status: StepState["status"] }) {
  if (status === "complete") return <CheckCircle2 className="text-green-600" size={22} />;
  if (status === "in_progress") return <Loader2 className="animate-spin text-brand-600" size={22} />;
  return <Circle className="text-zinc-300" size={22} />;
}

export function PipelineTimeline({ steps }: { steps: Record<StepName, StepState> }) {
  return (
    <div className="space-y-1">
      {STEP_ORDER.map((step, idx) => {
        const state = steps[step] ?? { status: "pending", data: null };
        const detail = stepDetail(step, state);
        const label = STEP_LABELS[step];
        return (
          <div key={step} className="flex gap-3">
            <div className="flex flex-col items-center">
              <StepIcon status={state.status} />
              {idx < STEP_ORDER.length - 1 && (
                <div className="my-1 h-6 w-px bg-zinc-200" />
              )}
            </div>
            <div className="flex-1 pb-4">
              <div className="flex items-center justify-between">
                <span
                  className={`text-sm font-semibold ${
                    state.status === "pending" ? "text-zinc-400" : "text-zinc-900"
                  }`}
                >
                  {label.title}
                </span>
                {state.completed_at && (
                  <span className="text-xs text-zinc-400">
                    {new Date(state.completed_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-500">{label.description}</p>
              {detail && (
                <div className="mt-1.5 rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1.5 text-xs text-zinc-600">
                  {detail}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
