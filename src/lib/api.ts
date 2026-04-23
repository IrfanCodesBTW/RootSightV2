import {
  ActionType,
  ApprovalStatus,
  EventType,
  type Action,
  type Hypothesis,
  type Impact,
  type Incident,
  type IncidentDetail,
  type IncidentStatus,
  type SeverityBand,
  type SimilarIncident,
  type TimelineEvent,
  type TriggerPayload,
} from "@/types/incident";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

interface ApiEnvelope<T> {
  success?: boolean;
  data: T;
  error?: string | null;
  code?: number;
}

interface BackendIncident {
  incident_id: string;
  title: string;
  severity?: string | null;
  status?: string | null;
  started_at?: string | null;
  detected_at?: string | null;
  resolved_at?: string | null;
}

interface BackendTimelineEvent {
  event_id: string;
  timestamp: string;
  description: string;
  event_type?: string;
  confidence?: number;
  evidence_source?: string;
}

interface BackendHypothesis {
  rank: number;
  statement: string;
  confidence_score?: number;
  supporting_evidence?: string[];
  contradicting_evidence?: string[];
}

interface BackendImpact {
  severity_band?: string;
  affected_services?: string[];
  estimated_requests_affected?: string | null;
  probable_user_impact?: string | null;
  business_impact_summary?: string | null;
}

interface BackendSimilarIncident {
  similar_to_id?: string;
  similarity_score?: number;
  why_similar?: string;
  previous_fix?: string;
}

interface BackendAction {
  action_id: string;
  action_type?: string;
  payload_preview?: string;
  full_payload?: Record<string, unknown>;
  approval_status?: string;
}

interface BackendPipelineState {
  incident_id: string;
  incident: BackendIncident;
  status?: string;
  timeline?: { events?: BackendTimelineEvent[] } | null;
  rca?: { hypotheses?: BackendHypothesis[] } | null;
  impact?: BackendImpact | null;
  memory?: { matches?: BackendSimilarIncident[] } | null;
  actions?: { actions?: BackendAction[] } | null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  if (!(options?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  const json = (await response.json()) as ApiEnvelope<T>;

  if (!response.ok || json.success === false || (json.error && json.success !== true)) {
    throw new Error(json.error ?? `Request failed with status ${response.status}`);
  }

  return json.data;
}

function mapSeverity(value?: string | null): SeverityBand {
  const normalized = (value ?? "").toLowerCase();
  if (normalized === "critical" || normalized === "p0" || normalized === "p1") return "critical";
  if (normalized === "high" || normalized === "p2") return "high";
  if (normalized === "medium" || normalized === "p3") return "medium";
  return "low";
}

function mapStatus(pipelineStatus?: string | null, incidentStatus?: string | null): IncidentStatus {
  const pipeline = (pipelineStatus ?? "").toLowerCase();
  const incident = (incidentStatus ?? "").toLowerCase();

  if (pipeline === "failed") return "failed";
  if (pipeline === "completed") return "completed";
  if (pipeline === "starting" || pipeline === "started") return "pending";
  if (pipeline) return "processing";

  if (incident === "resolved") return "completed";
  if (incident === "failed") return "failed";
  if (incident === "active" || incident === "investigating") return "processing";
  return "pending";
}

function mapStage(pipelineStatus?: string | null): string {
  const stage = (pipelineStatus ?? "").toLowerCase();
  const stageMap: Record<string, string> = {
    starting: "ingestion",
    started: "ingestion",
    building_timeline: "timeline",
    analyzing_rca: "rca",
    estimating_impact: "impact",
    searching_memory: "memory",
    drafting_actions: "actions",
    completed: "complete",
    failed: "actions",
  };

  return stageMap[stage] ?? "ingestion";
}

function mapProgress(pipelineStatus?: string | null): number {
  const stage = (pipelineStatus ?? "").toLowerCase();
  const progressMap: Record<string, number> = {
    starting: 5,
    started: 10,
    building_timeline: 25,
    analyzing_rca: 45,
    estimating_impact: 60,
    searching_memory: 75,
    drafting_actions: 90,
    completed: 100,
    failed: 100,
  };

  return progressMap[stage] ?? 0;
}

function mapEventType(value?: string): EventType {
  const normalized = (value ?? "unknown").toLowerCase();
  const known = new Set<string>(Object.values(EventType));
  return known.has(normalized) ? (normalized as EventType) : EventType.UNKNOWN;
}

function normalizeConfidence(value?: number): number {
  const raw = Number.isFinite(value) ? Number(value) : 0;
  return Math.max(0, Math.min(1, raw > 1 ? raw / 100 : raw));
}

function mapActionType(value?: string): ActionType {
  switch ((value ?? "").toLowerCase()) {
    case "jira_ticket":
      return ActionType.JIRA_DRAFT;
    case "slack_responder":
    case "slack_stakeholder":
      return ActionType.SLACK_DRAFT;
    case "confluence_rca":
      return ActionType.RUNBOOK;
    default:
      return ActionType.ESCALATION;
  }
}

function mapApprovalStatus(value?: string): ApprovalStatus {
  switch ((value ?? "").toLowerCase()) {
    case "approved":
      return ApprovalStatus.APPROVED;
    case "rejected":
      return ApprovalStatus.REJECTED;
    default:
      return ApprovalStatus.PENDING;
  }
}

function mapIncident(incident: BackendIncident, pipelineStatus?: string): Incident {
  const createdAt = incident.detected_at ?? incident.started_at ?? new Date().toISOString();

  return {
    id: incident.incident_id,
    title: incident.title,
    status: mapStatus(pipelineStatus, incident.status),
    severity: mapSeverity(incident.severity),
    created_at: createdAt,
    updated_at: incident.resolved_at ?? createdAt,
  };
}

function toNumber(value?: string | null): number {
  if (!value) return 0;
  const digits = value.replace(/[^\d]/g, "");
  if (!digits) return 0;
  const parsed = Number.parseInt(digits, 10);
  return Number.isFinite(parsed) ? parsed : 0;
}

function mapTimeline(events: BackendTimelineEvent[] = []): TimelineEvent[] {
  return events.map((event) => ({
    id: event.event_id,
    timestamp: event.timestamp,
    description: event.description,
    event_type: mapEventType(event.event_type),
    confidence: normalizeConfidence(event.confidence),
    source: event.evidence_source ?? "unknown",
  }));
}

function mapHypotheses(hypotheses: BackendHypothesis[] = []): Hypothesis[] {
  return hypotheses.map((hypothesis) => ({
    rank: hypothesis.rank,
    title: hypothesis.statement,
    description: hypothesis.statement,
    confidence: normalizeConfidence(hypothesis.confidence_score),
    evidence: hypothesis.supporting_evidence ?? [],
    counter_evidence: hypothesis.contradicting_evidence ?? [],
  }));
}

function mapImpact(impact?: BackendImpact | null): Impact | null {
  if (!impact) return null;

  return {
    severity_band: mapSeverity(impact.severity_band),
    affected_systems: impact.affected_services ?? [],
    estimated_users: toNumber(impact.estimated_requests_affected),
    business_impact: impact.business_impact_summary ?? impact.probable_user_impact ?? "Impact unavailable.",
    confidence: impact.severity_band ? 0.8 : 0.5,
  };
}

function mapSimilarIncidents(similar: BackendSimilarIncident[] = []): SimilarIncident[] {
  return similar.map((item) => ({
    incident_id: item.similar_to_id ?? "unknown",
    similarity_score: item.similarity_score ?? 0,
    title: item.why_similar ?? "Similar historical incident",
    resolution_summary: item.previous_fix ?? "No resolution summary available.",
  }));
}

function mapActions(actions: BackendAction[] = []): Action[] {
  return actions.map((action) => {
    const payload = action.full_payload ?? {};
    const payloadText = typeof payload.message === "string"
      ? payload.message
      : JSON.stringify(payload, null, 2);

    return {
      id: action.action_id,
      action_type: mapActionType(action.action_type),
      title: action.payload_preview ?? "Generated action",
      content: payloadText,
      approval_status: mapApprovalStatus(action.approval_status),
    };
  });
}

function toBackendSeverity(severity?: SeverityBand): string {
  if (severity === "critical") return "P1";
  if (severity === "high") return "P2";
  if (severity === "medium") return "P3";
  return "P4";
}

function toManualLogs(rawPayload: Record<string, unknown> | undefined): Array<Record<string, string>> | undefined {
  const logsValue = rawPayload?.logs;
  if (typeof logsValue !== "string" || !logsValue.trim()) return undefined;

  return logsValue
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => ({
      timestamp: new Date().toISOString(),
      level: "ERROR",
      message: line,
      service: typeof rawPayload?.service === "string" ? rawPayload.service : "unknown-service",
      host: "manual",
    }));
}

function toBackendTriggerPayload(payload: TriggerPayload): Record<string, unknown> {
  const rawPayload = payload.raw_payload;
  const service = typeof rawPayload?.service === "string" ? rawPayload.service : "unknown-service";
  const environment = typeof rawPayload?.environment === "string" ? rawPayload.environment : "production";
  const description = typeof rawPayload?.description === "string" ? rawPayload.description : payload.title;

  const backendPayload: Record<string, unknown> = {
    title: payload.title,
    service,
    severity: toBackendSeverity(payload.severity),
    environment,
    region: "us-east-1",
    source: payload.source,
    description,
    started_at: new Date().toISOString(),
  };

  const logs = toManualLogs(rawPayload);
  if (logs && logs.length > 0) {
    backendPayload.logs = logs;
  }

  return backendPayload;
}

export const checkHealth = () => request<{ status: string; version?: string }>("/health");

export const listIncidents = async (): Promise<Incident[]> => {
  const incidents = await request<BackendIncident[]>("/incidents");
  return incidents.map((incident) => mapIncident(incident));
};

export const getIncident = async (id: string): Promise<IncidentDetail> => {
  const state = await request<BackendPipelineState>(`/incident/${id}`);
  const incident = mapIncident(state.incident, state.status);

  return {
    ...incident,
    timeline: mapTimeline(state.timeline?.events ?? []),
    hypotheses: mapHypotheses(state.rca?.hypotheses ?? []),
    impact: mapImpact(state.impact),
    similar_incidents: mapSimilarIncidents(state.memory?.matches ?? []),
    actions: mapActions(state.actions?.actions ?? []),
    pipeline_stage: mapStage(state.status),
    pipeline_progress: mapProgress(state.status),
  };
};

export const triggerIncident = (payload: TriggerPayload) =>
  request<{ incident_id: string }>("/trigger", {
    method: "POST",
    body: JSON.stringify(toBackendTriggerPayload(payload)),
  });

export const uploadBundle = (file: File) => {
  const form = new FormData();
  form.append("file", file);

  return request<{ incident_id: string }>("/incident/upload", {
    method: "POST",
    body: form,
  });
};

export const draftRecoveryScript = (incidentId: string) =>
  request<{ script: string }>(`/incident/${incidentId}/draft-script`, {
    method: "POST",
  });
