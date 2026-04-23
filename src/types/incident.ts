export type IncidentStatus = "pending" | "processing" | "completed" | "failed";
export type SeverityBand = "critical" | "high" | "medium" | "low";

export enum EventType {
  DEPLOY = "deploy",
  ERROR_SPIKE = "error_spike",
  LATENCY_SPIKE = "latency_spike",
  CPU_SPIKE = "cpu_spike",
  MEMORY_SPIKE = "memory_spike",
  DB_FAILURE = "db_failure",
  TIMEOUT = "timeout",
  FAILOVER = "failover",
  RECOVERY = "recovery",
  ROLLBACK = "rollback",
  DEPENDENCY_FAILURE = "dependency_failure",
  CONFIG_CHANGE = "config_change",
  UNKNOWN = "unknown",
}

export enum ActionType {
  SLACK_DRAFT = "slack_draft",
  JIRA_DRAFT = "jira_draft",
  RUNBOOK = "runbook",
  ESCALATION = "escalation",
}

export enum ApprovalStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  description: string;
  event_type: EventType;
  confidence: number;
  source: string;
}

export interface Hypothesis {
  rank: number;
  title: string;
  description: string;
  confidence: number;
  evidence: string[];
  counter_evidence: string[];
}

export interface Impact {
  severity_band: SeverityBand;
  affected_systems: string[];
  estimated_users: number;
  business_impact: string;
  confidence: number;
}

export interface SimilarIncident {
  incident_id: string;
  similarity_score: number;
  title: string;
  resolution_summary: string;
}

export interface Action {
  id: string;
  action_type: ActionType;
  title: string;
  content: string;
  approval_status: ApprovalStatus;
}

export interface Incident {
  id: string;
  title: string;
  status: IncidentStatus;
  severity: SeverityBand;
  created_at: string;
  updated_at: string;
}

export interface IncidentDetail extends Incident {
  timeline: TimelineEvent[];
  hypotheses: Hypothesis[];
  impact: Impact | null;
  similar_incidents: SimilarIncident[];
  actions: Action[];
  pipeline_stage: string;
  pipeline_progress: number;
}

export interface TriggerPayload {
  title: string;
  source: "pagerduty" | "datadog" | "manual";
  severity?: SeverityBand;
  raw_payload?: Record<string, unknown>;
}
