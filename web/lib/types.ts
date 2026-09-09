export type EvidenceType =
  | "observed_fact"
  | "correlation"
  | "hypothesis"
  | "verified_finding"
  | "rejected_hypothesis"
  | "inconclusive_finding"
  | "notable_pattern"
  | "query_error";

export interface EvidenceEntry {
  id: string;
  entry_type: EvidenceType;
  step: string;
  sql: string | null;
  result_sample: unknown;
  claim: string;
  supports: string[];
  verifies_hypothesis: string | null;
  anomaly_id: string | null;
  key_metrics: Record<string, number | string> | null;
  timestamp: string;
  investigation_id?: string;
  title_id?: string;
}

export type StepName = "OBSERVE" | "INVESTIGATE" | "HYPOTHESIZE" | "VERIFY" | "BRIEF";
export type StepStatus = "pending" | "in_progress" | "complete";

export interface StepState {
  status: StepStatus;
  data: Record<string, unknown> | null;
  started_at?: string;
  completed_at?: string;
}

export interface Claim {
  text: string;
  citations: string[];
}

export interface RejectedHypothesis {
  text: string;
  citations: string[];
}

export interface Brief {
  summary: string;
  claims: Claim[];
  rejected_hypotheses: RejectedHypothesis[];
}

export type InvestigationStatus = "running" | "complete" | "error";

export interface Anomaly {
  anomaly_id: string;
  anomaly_type: string;
  region: string;
  metric: string;
  window_start_hour: number;
  window_end_hour: number;
  window_start_timestamp: string;
  window_end_timestamp: string;
  observed_value: number;
  baseline_range: Record<string, number>;
}

export type ReleaseStatus = "first_72_hours" | "post_72_hours" | "unknown";

export interface OverallPerformance {
  avg_completion_pct: number;
  baseline_completion_pct: number;
  delta_pct: number;
}

export interface Title {
  title_id: string;
  title_name: string;
  genre: string | null;
  runtime_min: number | null;
  release_datetime: string | null;
  release_type: string | null;
  regions: string[];
  release_status: ReleaseStatus;
  hours_since_release: number | null;
  overall_performance: OverallPerformance | null;
}

export interface InvestigationSummary {
  id: string;
  title_id: string;
  title: Title | null;
  status: InvestigationStatus;
  created_at: string;
  updated_at: string;
  steps: Record<StepName, StepState>;
  anomalies: Anomaly[];
  brief: Brief | null;
  validation_problems: string[];
  error: string | null;
}

export interface InvestigationDetail extends InvestigationSummary {
  evidence_log: EvidenceEntry[];
  events: PipelineEvent[];
}

export interface PipelineEvent {
  step: string;
  payload: {
    status?: string;
    [key: string]: unknown;
  };
  timestamp: string;
}

export interface BriefSummary {
  investigation_id: string;
  title_id: string;
  brief: Brief;
  validation_problems: string[];
  created_at: string;
}

export interface Overview {
  investigation_count: number;
  running_count: number;
  complete_count: number;
  brief_count: number;
  total_evidence_entries: number;
  investigations: InvestigationSummary[];
}
