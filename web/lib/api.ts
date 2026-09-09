import type {
  Overview,
  InvestigationSummary,
  InvestigationDetail,
  EvidenceEntry,
  BriefSummary,
} from "./types";


const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    cache: "no-store", // this data changes live; never let Next.js cache it
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  overview: () => apiFetch<Overview>("/overview"),

  listInvestigations: () => apiFetch<InvestigationSummary[]>("/investigations"),

  getInvestigation: (id: string) =>
    apiFetch<InvestigationDetail>(`/investigations/${id}`),

  startInvestigation: (titleId: string) =>
    apiFetch<{ investigation_id: string; status: string }>("/investigations", {
      method: "POST",
      body: JSON.stringify({ title_id: titleId }),
    }),

  searchEvidence: (params?: {
    investigation_id?: string;
    entry_type?: string;
    step?: string;
    q?: string;
  }) => {
    const qs = new URLSearchParams();
    if (params?.investigation_id) qs.set("investigation_id", params.investigation_id);
    if (params?.entry_type) qs.set("entry_type", params.entry_type);
    if (params?.step) qs.set("step", params.step);
    if (params?.q) qs.set("q", params.q);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return apiFetch<EvidenceEntry[]>(`/evidence${suffix}`);
  },

  getEvidenceDetail: (investigationId: string, evidenceId: string) =>
    apiFetch<EvidenceEntry>(`/evidence/${investigationId}/${evidenceId}`),

  listBriefs: () => apiFetch<BriefSummary[]>("/briefs"),

  eventsUrl: (investigationId: string) =>
    `${API_BASE}/investigations/${investigationId}/events`,
};
