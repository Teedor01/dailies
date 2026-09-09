import type { Title } from "@/lib/types";

function formatRuntime(min: number | null): string | null {
  if (min == null) return null;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatReleaseDate(iso: string | null): string | null {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function formatPlatform(releaseType: string | null): string | null {
  if (!releaseType) return null;
  return releaseType === "theatrical" ? "Theatrical" : releaseType === "streaming" ? "Streaming" : releaseType;
}

function formatStatus(status: Title["release_status"], hoursSince: number | null): { label: string; detail: string } {
  if (status === "first_72_hours") {
    return {
      label: "FIRST 72 HOURS",
      detail: hoursSince != null ? `${hoursSince}h into release window` : "Release window in progress",
    };
  }
  if (status === "post_72_hours") {
    return { label: "FIRST 72 HOURS", detail: "Release window complete" };
  }
  return { label: "RELEASE WINDOW", detail: "Timing unknown" };
}

export function MovieHeader({ title }: { title: Title | null }) {
  if (!title) {
    return (
      <div className="mb-6 rounded-xl border border-zinc-200 bg-white p-4 text-sm text-zinc-400">
        Loading release details...
      </div>
    );
  }

  const chips = [
    title.genre,
    formatRuntime(title.runtime_min),
    formatReleaseDate(title.release_datetime),
    formatPlatform(title.release_type),
  ].filter(Boolean) as string[];

  const perf = title.overall_performance;

  return (
    <div className="mb-6 rounded-xl border border-zinc-200 bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl leading-none">🎬</span>
            <h1 className="text-xl font-bold text-zinc-900">{title.title_name}</h1>
          </div>
          {chips.length > 0 && (
            <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
              {chips.map((c) => (
                <span key={c} className="rounded-md bg-zinc-100 px-2 py-0.5 font-medium text-zinc-600">
                  {c}
                </span>
              ))}
            </div>
          )}
          <p className="mt-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
            {formatStatus(title.release_status, title.hours_since_release).label}
          </p>
          <p className="text-xs text-zinc-500">{formatStatus(title.release_status, title.hours_since_release).detail}</p>
        </div>

        {perf && (
          <div className="shrink-0 rounded-lg border border-zinc-100 bg-zinc-50 px-4 py-2.5 text-right">
            <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">Overall performance</div>
            <div
              className={`mt-0.5 text-lg font-bold ${
                perf.delta_pct < -0.03 ? "text-red-600" : perf.delta_pct > 0.03 ? "text-emerald-600" : "text-zinc-900"
              }`}
            >
              {(perf.avg_completion_pct * 100).toFixed(1)}% completion
            </div>
            <div className="text-[11px] text-zinc-500">
              vs {(perf.baseline_completion_pct * 100).toFixed(1)}% baseline (
              {perf.delta_pct >= 0 ? "+" : ""}
              {(perf.delta_pct * 100).toFixed(1)}pt)
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
