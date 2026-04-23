/**
 * Backward-compatible re-exports from the canonical types in @/types/index.
 * Components that previously imported from @/types/incident should continue to work.
 */
export type {
  Severity,
  IncidentStatus,
  PipelineStepStatus,
  PipelineStepState,
  PipelineState,
  RawEvent,
  Event,
  Hypothesis,
  Impact,
  SimilarIncident,
  Action,
  Incident,
  TriggerPipelineRequest,
  TriggerPipelineResponse,
  ListIncidentsResponse,
  GetIncidentResponse,
  GetIncidentStatusResponse,
  DraftRecoveryScriptResponse,
  SeverityBand,
  ApiResponse,
} from "./index";

export { PIPELINE_STEPS, PipelineStepStatus as PipelineStepStatusEnum } from "./index";

// Backward-compatible aliases for components using the old type names
import type { Incident as _Incident, Event as _Event } from "./index";

/** @deprecated Use `Incident` instead */
export type IncidentDetail = _Incident;

/** @deprecated Use `Event` instead */
export type TimelineEvent = _Event;

// Re-export enums for components using enum-style types
// Aligned with Python: src/schemas/event.py → EventType
export const EventType = {
  DEPLOY: "deploy",
  ERROR_SPIKE: "error_spike",
  LATENCY_SPIKE: "latency_spike",
  CPU_SPIKE: "cpu_spike",
  MEMORY_SPIKE: "memory_spike",
  DB_FAILURE: "db_failure",
  TIMEOUT: "timeout",
  FAILOVER: "failover",
  RECOVERY: "recovery",
  ROLLBACK: "rollback",
  DEPENDENCY_FAILURE: "dependency_failure",
  CONFIG_CHANGE: "config_change",
  UNKNOWN: "unknown",
} as const;

// Aligned with Python: src/schemas/action.py → ActionType
export const ActionType = {
  JIRA_TICKET: "jira_ticket",
  SLACK_RESPONDER: "slack_responder",
  SLACK_STAKEHOLDER: "slack_stakeholder",
  CONFLUENCE_RCA: "confluence_rca",
  MANUAL_REVIEW: "manual_review",
} as const;

// Aligned with Python: src/schemas/action.py → ApprovalStatus
export const ApprovalStatus = {
  PENDING: "pending_approval",
  APPROVED: "approved",
  REJECTED: "rejected",
} as const;

// Aligned with Python: src/schemas/action.py → ExecutionStatus
export const ExecutionStatus = {
  DRAFT: "draft",
  SENT: "sent",
  FAILED: "failed",
} as const;
