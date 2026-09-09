import Link from "next/link";
import type { InvestigationSummary } from "@/lib/types";
import { deriveReleaseHealth, releaseHealthStyle } from "@/lib/releaseHealth";

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function formatRuntime(min: number | null): string | null {
  if (min == null) return null;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}


export function ReleaseOverviewCard({ titleId, latest }: { titleId: string; latest: InvestigationSummary | null }) {
  const title = latest?.title;
  const health = deriveReleaseHealth(latest);
  const style = releaseHealthStyle(health);

  const anomalyCount = latest?.anomalies.length ?? 0;
  const isRunning = latest?.status === "running";

  const chips = [
    title?.genre,
    formatRuntime(title?.runtime_min ?? null),
    title?.release_datetime ? new Date(title.release_datetime).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : null,
    title?.release_status === "first_72_hours" ? "First 72 hours" : title?.release_status === "post_72_hours" ? "Past 72 hours" : null,
  ].filter(Boolean) as string[];

  return (
    <Link
      href={`/releases/${titleId}`}
      className="block rounded-xl border border-zinc-200 bg-white p-5 transition hover:border-zinc-300 hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg leading-none">🎬</span>
            <h3 className="text-lg font-bold text-zinc-900">{title?.title_name ?? titleId}</h3>
          </div>
          {chips.length > 0 && (
            <p className="mt-1 text-xs text-zinc-500">{chips.join(" · ")}</p>
          )}
        </div>
        <span className={`shrink-0 rounded-md px-2 py-1 text-xs font-bold tracking-wide ${style.bg} ${style.text}`}>
          {style.label}
        </span>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-zinc-500">
        <span>
          {anomalyCount} anomal{anomalyCount === 1 ? "y" : "ies"} detected
        </span>
        {isRunning && <span className="font-medium text-amber-600">1 active investigation</span>}
        {latest && <span>Last checked: {timeAgo(latest.updated_at)}</span>}
      </div>

      <div className="mt-3 text-sm font-medium text-brand-700">View Release &rarr;</div>
    </Link>
  );
}
