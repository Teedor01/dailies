import type { InvestigationStatus } from "@/lib/types";

const STYLES: Record<InvestigationStatus, { bg: string; text: string; label: string }> = {
  running: { bg: "bg-blue-50", text: "text-blue-700", label: "Investigating" },
  complete: { bg: "bg-green-50", text: "text-green-700", label: "Brief Ready" },
  error: { bg: "bg-red-50", text: "text-red-700", label: "Error" },
};

export function StatusBadge({ status }: { status: InvestigationStatus }) {
  const style = STYLES[status] ?? STYLES.running;
  return (
    <span
      className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}
