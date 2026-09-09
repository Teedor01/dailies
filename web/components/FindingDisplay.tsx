import { useState } from "react";
import { formatPercentValue, formatNumber } from "@/lib/format";

export const VERDICT_LABEL: Record<string, string> = {
  verified_finding: "SUPPORTED",
  rejected_hypothesis: "CONTRADICTED",
  inconclusive_finding: "INCONCLUSIVE",
};

export const VERDICT_STYLE: Record<string, string> = {
  verified_finding: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected_hypothesis: "bg-red-50 text-red-700 border-red-200",
  inconclusive_finding: "bg-amber-50 text-amber-700 border-amber-200",
};


export function EvidenceCount({ ids, onOpen }: { ids: string[]; onOpen: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  if (ids.length === 0) return null;
  return (
    <div className="mt-2">
      <button onClick={() => setOpen((o) => !o)} className="text-xs font-medium text-zinc-400 hover:text-zinc-600">
        {open ? "Hide sources" : `${ids.length} supporting record${ids.length === 1 ? "" : "s"} \u00b7 View evidence`}
      </button>
      {open && (
        <div className="mt-1 flex flex-wrap gap-1">
          {ids.map((id) => (
            <button
              key={id}
              onClick={() => onOpen(id)}
              className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-mono text-[11px] text-zinc-600 hover:bg-zinc-200"
            >
              {id}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}


export function MetricComparison({ metrics }: { metrics: Record<string, number | string> }) {
  const groupA: [string, number | string][] = [];
  const groupB: [string, number | string][] = [];
  for (const [key, value] of Object.entries(metrics)) {
    if (key === "group_a_label" || key === "group_b_label") continue;
    if (key.startsWith("group_a_")) groupA.push([key.replace("group_a_", ""), value]);
    if (key.startsWith("group_b_")) groupB.push([key.replace("group_b_", ""), value]);
  }
  const labelA = (metrics.group_a_label as string) ?? "Group A";
  const labelB = (metrics.group_b_label as string) ?? "Comparison";

  const fmt = (field: string, value: number | string) => {
    if (typeof value !== "number") return String(value);
    return field.includes("pct") ? formatPercentValue(value) : formatNumber(value);
  };
  const fieldLabel = (field: string) => field.replace(/_pct$/, "").replace(/_/g, " ");

  const columns: [string, [string, number | string][]][] = [
    [labelA, groupA],
    [labelB, groupB],
  ];

  return (
    <div className="mt-2 grid grid-cols-2 gap-3">
      {columns.map(([label, fields], i) => (
        <div key={i} className={`rounded-lg p-3 ${i === 0 ? "bg-red-50" : "bg-zinc-50"}`}>
          <div className={`text-xs font-bold ${i === 0 ? "text-red-700" : "text-zinc-600"}`}>{label}</div>
          <div className="mt-1 space-y-0.5">
            {fields.map(([field, value]) => (
              <div key={field} className="text-xs text-zinc-600">
                <span className="font-semibold">{fmt(field, value)}</span> {fieldLabel(field)}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
