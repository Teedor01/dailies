"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/api";
import { useInvestigationEvents } from "@/lib/useInvestigationEvents";
import type { InvestigationDetail, EvidenceEntry } from "@/lib/types";
import { buildHeroNarrative, buildReleaseTakeaway } from "@/lib/narrative";
import { StatusBadge } from "@/components/StatusBadge";
import { EvidenceTypeBadge } from "@/components/EvidenceTypeBadge";
import { PipelineTimeline } from "@/components/PipelineTimeline";
import { EvidenceDetailPanel } from "@/components/EvidenceDetailPanel";
import { MovieHeader } from "@/components/MovieHeader";
import { groupFindings } from "@/components/ReleaseFindingCard";
import { AnomalyStoryCard } from "@/components/AnomalyStoryCard";
import { InvestigationNarrative } from "@/components/InvestigationNarrative";

type Tab = "story" | "timeline" | "evidence";

export default function InvestigationDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const searchParams = useSearchParams();
  const [investigation, setInvestigation] = useState<InvestigationDetail | null>(null);
  const [tab, setTab] = useState<Tab>("story");
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceEntry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAnomalyId, setSelectedAnomalyId] = useState<string | null>(searchParams.get("anomaly"));

  const { refreshSignal } = useInvestigationEvents(id);

  const load = useCallback(async () => {
    try {
      const result = await api.getInvestigation(id);
      setInvestigation(result);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load investigation");
    }
  }, [id]);


  useEffect(() => {
    load();
  }, [load, refreshSignal]);

  if (error) {
    return (
      <div className="p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      </div>
    );
  }
  if (!investigation) {
    return <div className="p-8 text-sm text-zinc-400">Loading...</div>;
  }

  const allFindingGroups = groupFindings(investigation.evidence_log);
  const evidenceById = new Map(investigation.evidence_log.map((e) => [e.id, e]));
  const anomalies = investigation.anomalies;
  const activeAnomalyId = selectedAnomalyId ?? anomalies[0]?.anomaly_id ?? null;
  const anomaly = anomalies.find((a) => a.anomaly_id === activeAnomalyId) ?? anomalies[0];
  const findingGroups = activeAnomalyId
    ? allFindingGroups.filter((g) => g.hypothesis.anomaly_id === activeAnomalyId)
    : allFindingGroups;
  const movieName = investigation.title?.title_name ?? investigation.title_id;
  const notableEntries = investigation.evidence_log.filter(
    (e) => e.entry_type === "notable_pattern" && e.anomaly_id === activeAnomalyId
  );
  const hero = buildHeroNarrative(investigation);
  const takeaway = buildReleaseTakeaway(investigation);

  const openEvidence = (entryId: string) => {
    const entry = evidenceById.get(entryId);
    if (entry) {
      setSelectedEvidence(entry);
      setTab("evidence");
    }
  };

  const focusAnomaly = (anomalyId: string) => {
    setSelectedAnomalyId(anomalyId);
    setTab("story");
    setTimeout(() => document.getElementById("dailies-investigation")?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  return (
    <div className="p-8">
      <Link href="/investigations" className="mb-3 flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-700">
        <ChevronLeft size={16} />
        Investigations
      </Link>

      <MovieHeader title={investigation.title} />

      <div className="mb-4 flex gap-1 border-b border-zinc-200">
        {(["story", "timeline", "evidence"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium capitalize ${
              tab === t ? "border-b-2 border-brand-600 text-brand-700" : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            {t}
          </button>
        ))}
        <span className="ml-auto flex items-center">
          <StatusBadge status={investigation.status} />
        </span>
      </div>

      {tab === "story" && (
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <p className="text-base text-zinc-800">{hero.overview}</p>
          </div>

          {anomalies.length > 0 && (
            <div>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
                What happened to {movieName}?
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {anomalies.map((a) => (
                  <AnomalyStoryCard
                    key={a.anomaly_id}
                    anomaly={a}
                    evidenceLog={investigation.evidence_log}
                    onViewInvestigation={() => focusAnomaly(a.anomaly_id)}
                  />
                ))}
              </div>
            </div>
          )}

          {anomaly && (
            <div id="dailies-investigation">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">Dailies&rsquo; investigation</h2>
                {anomalies.length > 1 && (
                  <div className="flex flex-wrap gap-2">
                    {anomalies.map((a) => (
                      <button
                        key={a.anomaly_id}
                        onClick={() => setSelectedAnomalyId(a.anomaly_id)}
                        className={`rounded-lg border px-3 py-1 text-xs font-medium ${
                          a.anomaly_id === activeAnomalyId
                            ? "border-brand-600 bg-brand-50 text-brand-700"
                            : "border-zinc-200 bg-white text-zinc-600 hover:bg-zinc-50"
                        }`}
                      >
                        {a.region} &middot; {a.metric}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <InvestigationNarrative
                movieName={movieName}
                anomaly={anomaly}
                totalAnomalyCount={anomalies.length}
                findingGroups={findingGroups}
                onSelectEvidence={openEvidence}
              />

              {notableEntries.length > 0 && (
                <div className="mt-4 space-y-3">
                  {notableEntries.map((e) => (
                    <div key={e.id} className="rounded-xl border border-sky-200 bg-sky-50 p-4">
                      <div className="text-xs font-bold uppercase tracking-wide text-sky-700">Notable pattern</div>
                      <p className="mt-1 text-sm text-sky-900">{e.claim}</p>
                      <button
                        onClick={() => openEvidence(e.id)}
                        className="mt-2 text-xs font-medium text-sky-700 hover:text-sky-900"
                      >
                        View evidence &rarr;
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="rounded-xl border border-zinc-200 bg-white p-5">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500">Release takeaway</h2>
            <p className="text-sm text-zinc-800">{takeaway.paragraph}</p>
            {takeaway.priority && (
              <div className="mt-3 rounded-lg bg-amber-50 p-3">
                <div className="text-xs font-bold uppercase tracking-wide text-amber-800">
                  Priority: {takeaway.priority.region}
                </div>
                <p className="mt-1 text-sm text-amber-900">{takeaway.priority.text}</p>
              </div>
            )}
            {takeaway.alsoMonitor.map((m) => (
              <div key={m.region} className="mt-2 rounded-lg bg-zinc-50 p-3">
                <div className="text-xs font-bold uppercase tracking-wide text-zinc-500">Also monitor: {m.region}</div>
                <p className="mt-1 text-sm text-zinc-700">{m.text}</p>
              </div>
            ))}
          </div>

          {investigation.brief && (
            <details className="rounded-xl border border-zinc-200 bg-white p-4">
              <summary className="cursor-pointer text-sm font-medium text-zinc-500 hover:text-zinc-700">
                Dailies&rsquo; release investigation
              </summary>
              <div className="mt-4">
                {investigation.validation_problems.length > 0 && (
                  <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                    <div className="mb-1 font-semibold">Validation issues</div>
                    <ul className="list-inside list-disc space-y-0.5">
                      {investigation.validation_problems.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="mb-4 text-sm text-zinc-700">{investigation.brief.summary}</p>
                <ul className="space-y-2">
                  {investigation.brief.claims.map((c, i) => (
                    <li key={i} className="rounded-lg border border-zinc-100 bg-zinc-50 p-3 text-sm text-zinc-700">
                      {c.text}
                      <div className="mt-1.5 flex gap-1">
                        {c.citations.map((cid) => (
                          <button
                            key={cid}
                            onClick={() => openEvidence(cid)}
                            className="rounded-md bg-white border border-zinc-200 px-1.5 py-0.5 font-mono text-[11px] text-zinc-600 hover:bg-zinc-100"
                          >
                            {cid}
                          </button>
                        ))}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </details>
          )}
        </div>
      )}

      {tab === "timeline" && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 rounded-xl border border-zinc-200 bg-white p-4">
            <PipelineTimeline steps={investigation.steps} />
          </div>
          {anomaly && (
            <div className="rounded-xl border border-zinc-200 bg-white p-4">
              <h3 className="mb-3 text-sm font-semibold text-zinc-900">Anomaly Summary</h3>
              <dl className="space-y-2.5 text-xs">
                <Row label="Anomaly ID" value={anomaly.anomaly_id} mono />
                <Row label="Type" value={anomaly.anomaly_type} />
                <Row label="Region" value={anomaly.region} />
                <Row label="Metric" value={anomaly.metric} />
                <Row label="Observed" value={String(anomaly.observed_value)} />
                <Row label="Window" value={`${anomaly.window_start_timestamp} \u2192 ${anomaly.window_end_timestamp}`} />
              </dl>
            </div>
          )}
        </div>
      )}

      {tab === "evidence" && (
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl border border-zinc-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 text-xs text-zinc-500">
                  <th className="px-3 py-2 font-medium">ID</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                  <th className="px-3 py-2 font-medium">Step</th>
                </tr>
              </thead>
              <tbody>
                {investigation.evidence_log.map((entry) => (
                  <tr
                    key={entry.id}
                    onClick={() => setSelectedEvidence(entry)}
                    className={`cursor-pointer border-b border-zinc-100 last:border-0 hover:bg-zinc-50 ${
                      selectedEvidence?.id === entry.id ? "bg-brand-50" : ""
                    }`}
                  >
                    <td className="px-3 py-2 font-mono text-xs text-zinc-700">{entry.id}</td>
                    <td className="px-3 py-2">
                      <EvidenceTypeBadge type={entry.entry_type} />
                    </td>
                    <td className="px-3 py-2 text-xs text-zinc-500">{entry.step}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            {selectedEvidence ? (
              <EvidenceDetailPanel entry={selectedEvidence} />
            ) : (
              <p className="p-8 text-center text-sm text-zinc-400">Select an evidence entry to inspect it.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <dt className="text-zinc-500">{label}</dt>
      <dd className={`text-right text-zinc-700 ${mono ? "font-mono" : "font-medium"}`}>{value}</dd>
    </div>
  );
}
