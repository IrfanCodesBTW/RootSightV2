// ============================================================================
// RootSight V3 — Canonical TypeScript Types
// Aligned with Python Pydantic schemas (source of truth)
// ============================================================================

// ── Enums ───────────────────────────────────────────────────────────────────────

/** Matches Python: src/schemas/incident.py → Severity */
export enum Severity {
  P0 = "P0",
  P1 = "P1",
  P2 = "P2",
  P3 = "P3",
  P4 = "P4",
}

/** Matches Python: src/schemas/incident.py → IncidentStatus (lowercase values) */
export enum IncidentStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  PARTIAL = "partial",
  DEGRADED = "degraded",
}

/** Pipeline step status — used by the orchestrator */
export enum PipelineStepStatus {
  PENDING = "PENDING",
  RUNNING = "RUNNING",
  COMPLETE = "COMPLETE",
  FAILED = "FAILED",
}

/** Matches Python: src/schemas/impact.py → SeverityBand */
export type SeverityBand = "critical" | "high" | "medium" | "low";

// ── Pipeline State ──────────────────────────────────────────────────────────────

export interface PipelineStepState {
  status: PipelineStepStatus;
  started_at?: string;
  completed_at?: string;
}

export interface PipelineState {
  ingestion: PipelineStepState;
  timeline: PipelineStepState;
  rca: PipelineStepState;
  impact: PipelineStepState;
  memory: PipelineStepState;
  actions: PipelineStepState;
}

export const PIPELINE_STEPS: { key: keyof PipelineState; label: string }[] = [
  { key: "ingestion", label: "Ingestion" },
  { key: "timeline", label: "Timeline" },
  { key: "rca", label: "RCA" },
  { key: "impact", label: "Impact" },
  { key: "memory", label: "Memory" },
  { key: "actions", label: "Actions" },
];

// ── Domain Models (aligned with Python Pydantic schemas) ────────────────────────

/** Raw log event from ingestion — matches ingestion_service.py → RawEvent */
export interface RawEvent {
  timestamp: string;
  level: string;
  message: string;
  source: string;
  service: string;
}

/** Structured timeline event — matches schemas/event.py → Event */
export interface Event {
  event_id: string;
  incident_id: string;
  timestamp: string;
  event_type: string;
  description: string;
  evidence_source: string;
  confidence: number;
  raw_reference?: string;
}

/** Root cause hypothesis — matches schemas/hypothesis.py → Hypothesis */
export interface Hypothesis {
  hypothesis_id: string;
  incident_id: string;
  rank: number;
  statement: string;
  confidence_score: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  missing_information: string[];
  recommended_check?: string;
  severity_band?: string | null;
}

/** Impact assessment — matches schemas/impact.py → Impact */
export interface Impact {
  incident_id: string;
  affected_services: string[];
  affected_users: number;
  severity_band: SeverityBand;
  estimated_duration_minutes?: number | null;
  probable_user_impact: string;
  estimated_requests_affected?: string | null;
  business_impact_summary?: string | null;
}

/** Similar past incident — matches schemas/similar_incident.py → SimilarIncident */
export interface SimilarIncident {
  incident_id: string;
  similar_to_id: string;
  similarity_score: number;
  why_similar: string;
  previous_fix: string;
}

/** Remediation action — matches schemas/action.py → Action */
export interface Action {
  action_id: string;
  incident_id: string;
  action_type: string;
  destination: string;
  payload_preview: string;
  full_payload: Record<string, unknown>;
  approval_status: string;
  execution_status: string;
}

// ── Composite Incident (pipeline state response) ────────────────────────────────

export interface Incident {
  incident_id: string;
  status: IncidentStatus | string;
  pipeline_steps: PipelineState;
  current_step?: string;
  incident: {
    incident_id: string;
    title: string;
    service: string;
    severity: Severity | string;
    environment: string;
    region: string;
    source: string;
    description?: string | null;
    started_at: string;
    detected_at: string;
    resolved_at?: string | null;
    status: IncidentStatus | string;
  } | null;
  timeline: {
    events: Event[];
    timeline_confidence: number;
    gaps_detected: number;
    total_events: number;
    analysis_note?: string | null;
  } | null;
  rca: {
    hypotheses: Hypothesis[];
    analysis_confidence: number;
    is_low_confidence: boolean;
    analysis_note?: string | null;
  } | null;
  impact: Impact | null;
  memory: {
    matches: SimilarIncident[];
  } | null;
  actions: {
    actions: Action[];
  } | null;
  error?: string | null;
  started_at?: string;
  completed_at?: string | null;
}

// ── API Request/Response Types ──────────────────────────────────────────────────

export interface TriggerPipelineRequest {
  title?: string;
  severity?: Severity | string;
  source?: string;
  payload?: string;
  bundle_file?: string;
}

export interface TriggerPipelineResponse {
  incident_id: string;
  status: string;
}

export interface ListIncidentsResponse {
  items: Incident[];
  total: number;
  page: number;
  limit: number;
}

export interface GetIncidentResponse {
  success: boolean;
  data: Incident | null;
  error: string | null;
}

export interface GetIncidentStatusResponse {
  success: boolean;
  data: Incident | null;
  error: string | null;
}

export interface DraftRecoveryScriptResponse {
  success: boolean;
  data: { script: string } | null;
  error: string | null;
}

// ── API Envelope ────────────────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  error: string | null;
}
