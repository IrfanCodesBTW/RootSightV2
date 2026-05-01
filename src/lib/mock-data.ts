/**
 * Mock data generators for demo mode.
 * Field names are aligned with Python Pydantic schema model_dump() output.
 */
import {
  IncidentStatus,
  Severity,
  PipelineStepStatus,
} from "@/types";
import type {
  Incident,
  Event,
  Hypothesis,
  Impact,
  SimilarIncident,
  Action,
  PipelineState,
} from "@/types";

// ── Helpers ─────────────────────────────────────────────────────────────────────

function randomId(): string {
  return Math.random().toString(36).substring(2, 10);
}

function minutesAgo(n: number): string {
  return new Date(Date.now() - n * 60_000).toISOString();
}

// ── Completed pipeline state ────────────────────────────────────────────────────

function makeCompletedPipelineState(): PipelineState {
  return {
    ingestion: { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(10), completed_at: minutesAgo(9) },
    timeline:  { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(9),  completed_at: minutesAgo(7) },
    rca:       { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(7),  completed_at: minutesAgo(5) },
    impact:    { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(5),  completed_at: minutesAgo(4) },
    memory:    { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(4),  completed_at: minutesAgo(3) },
    actions:   { status: PipelineStepStatus.COMPLETE, started_at: minutesAgo(3),  completed_at: minutesAgo(2) },
  };
}

// ── Mock Events ─────────────────────────────────────────────────────────────────

function makeMockEvents(incidentId: string): Event[] {
  return [
    {
      event_id: randomId(),
      incident_id: incidentId,
      timestamp: minutesAgo(8),
      event_type: "deploy",
      description: "Deployment v2.4.1 pushed to us-east-1",
      evidence_source: "deploy-bot",
      confidence: 95,
    },
    {
      event_id: randomId(),
      incident_id: incidentId,
      timestamp: minutesAgo(7),
      event_type: "latency_spike",
      description: "p99 latency jumped to 1200ms on content-delivery",
      evidence_source: "datadog-metrics",
      confidence: 88,
    },
    {
      event_id: randomId(),
      incident_id: incidentId,
      timestamp: minutesAgo(6),
      event_type: "error_spike",
      description: "502 error rate exceeded 15% on CDN edge",
      evidence_source: "cdn-logs",
      confidence: 92,
    },
    {
      event_id: randomId(),
      incident_id: incidentId,
      timestamp: minutesAgo(4),
      event_type: "cpu_spike",
      description: "Origin server CPU hit 98%",
      evidence_source: "host-metrics",
      confidence: 90,
    },
  ];
}

// ── Mock Hypotheses ─────────────────────────────────────────────────────────────

function makeMockHypotheses(incidentId: string): Hypothesis[] {
  return [
    {
      id: randomId(),
      text: "Cache purge triggered thundering herd on origin",
      supporting_event_ids: [randomId(), randomId(), randomId()],
      evidence_strength: "strong",
      confidence: "high",
      category: "infrastructure",
      recommended_action_hint: "Review CDN purge policy and origin autoscaling",
    },
    {
      id: randomId(),
      text: "Deployment v2.4.1 introduced regression in request handling",
      supporting_event_ids: [randomId()],
      evidence_strength: "weak",
      confidence: "medium",
      category: "application",
      recommended_action_hint: "Compare request handling between versions",
    },
  ];
}

// ── Mock Impact ─────────────────────────────────────────────────────────────────

function makeMockImpact(incidentId: string): Impact {
  return {
    incident_id: incidentId,
    affected_services: ["content-delivery", "cdn-edge", "origin-server"],
    affected_users: 45000,
    severity_band: "critical",
    estimated_duration_minutes: 12,
    probable_user_impact: "Users experienced 502 errors and degraded page loads for ~12 minutes",
    estimated_requests_affected: "~2.1M requests",
    business_impact_summary: "Critical: 45K users affected with 502s during peak hours. Estimated revenue impact: $18K.",
  };
}

// ── Mock Similar Incidents ──────────────────────────────────────────────────────

function makeMockSimilarIncidents(incidentId: string): SimilarIncident[] {
  return [
    {
      incident_id: incidentId,
      similar_to_id: "HIST-001",
      similarity_score: 0.89,
      why_similar: "Both involve CDN cache purge causing thundering herd on origin servers",
      previous_fix: "Implemented staged CDN purge with 10% rollout per region",
    },
    {
      incident_id: incidentId,
      similar_to_id: "HIST-003",
      similarity_score: 0.72,
      why_similar: "Similar CPU exhaustion pattern from connection pool issues",
      previous_fix: "Added statement_timeout=30000ms. Migrations now run in maintenance window.",
    },
  ];
}

// ── Mock Actions ────────────────────────────────────────────────────────────────

function makeMockActions(incidentId: string): Action[] {
  return [
    {
      action_id: randomId(),
      incident_id: incidentId,
      action_type: "jira_ticket",
      destination: "PLATFORM-BOARD",
      payload_preview: "Investigate CDN cache purge causing 502 storm",
      full_payload: {
        title: "[P1] CDN Cache Purge 502 Storm — Root Cause Investigation",
        description: "Automated ticket from RootSight. Top hypothesis: Cache purge triggered thundering herd.",
        priority: "P1",
      },
      approval_status: "pending_approval",
      execution_status: "draft",
    },
    {
      action_id: randomId(),
      incident_id: incidentId,
      action_type: "slack_responder",
      destination: "#incident-response",
      payload_preview: "Incident update: CDN 502 storm — origin CPU overloaded",
      full_payload: {
        message: "🔴 *P1 Incident Update*\n*CDN Cache Purge 502 Storm*\nTop cause: Cache purge triggered thundering herd on origin (87% confidence)\nAffected: 45K users\nAction: Staged rollback recommended",
      },
      approval_status: "pending_approval",
      execution_status: "draft",
    },
  ];
}

// ── Main Generator ──────────────────────────────────────────────────────────────

export function generateMockIncident(incidentId?: string): Incident {
  const id = incidentId ?? `mock-${randomId()}`;

  return {
    incident_id: id,
    status: IncidentStatus.COMPLETED,
    pipeline_steps: makeCompletedPipelineState(),
    current_step: "actions",
    incident: {
      incident_id: id,
      title: "CDN Cache Purge 502 Storm",
      service: "content-delivery",
      severity: Severity.P1,
      environment: "production",
      region: "us-east-1",
      source: "datadog",
      description: "Full CDN cache purge triggered 502 errors across edge nodes",
      started_at: minutesAgo(10),
      detected_at: minutesAgo(9),
      resolved_at: null,
      status: IncidentStatus.COMPLETED,
    },
    timeline: {
      events: makeMockEvents(id),
      timeline_confidence: 85,
      gaps_detected: 1,
      total_events: 4,
      analysis_note: null,
    },
    rca: {
      hypotheses: makeMockHypotheses(id),
      insufficient_data: false,
    },
    impact: makeMockImpact(id),
    memory: {
      matches: makeMockSimilarIncidents(id),
    },
    actions: {
      actions: makeMockActions(id),
    },
    error: null,
    started_at: minutesAgo(10),
    completed_at: minutesAgo(2),
  };
}
