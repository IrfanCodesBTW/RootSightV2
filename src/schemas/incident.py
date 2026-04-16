"""
RootSight — Incident Schemas

Core models: IncidentHeader (input), IncidentBrief (final composite output),
AgentStatus (pipeline tracking).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DeployMarker(BaseModel):
    """A deployment event associated with the incident time window."""
    version: str = Field(..., description="Deployed version tag")
    deployed_at: str = Field(..., description="ISO-8601 deployment timestamp")
    deployer: str = Field(default="unknown", description="Who or what triggered the deploy")


class IncidentHeader(BaseModel):
    """
    Parsed alert that initiates the pipeline.
    Produced by the Trigger Agent.
    """
    incident_id: str = Field(..., description="Unique incident identifier")
    service: str = Field(..., description="Primary affected service")
    alert_title: str = Field(..., description="Short alert title from monitoring tool")
    severity: str = Field(..., description="Severity level: P1, P2, P3, or P4")
    timestamp: str = Field(..., description="ISO-8601 alert timestamp")
    source: str = Field(default="pagerduty", description="Alert source system")
    environment: str = Field(default="production", description="Environment: production, staging, etc.")
    region: str = Field(default="us-east-1", description="Deployment region")
    description: str = Field(default="", description="Extended alert description")
    deploy_markers: list[DeployMarker] = Field(default_factory=list, description="Recent deployments near alert time")


class AgentStatus(BaseModel):
    """Tracks success/failure of each pipeline agent."""
    trigger: str = Field(default="pending")
    log: str = Field(default="pending")
    timeline: str = Field(default="pending")
    rca: str = Field(default="pending")
    impact: str = Field(default="pending")
    memory: str = Field(default="pending")
    action: str = Field(default="pending")


class IncidentBrief(BaseModel):
    """
    Final composite output of the full pipeline.
    Assembled by the Manager Agent.
    """
    incident_id: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    processing_time_seconds: float = Field(default=0.0)

    header: Optional[dict] = None
    timeline: Optional[dict] = None
    hypotheses: Optional[dict] = None
    impact: Optional[dict] = None
    similar_incidents: Optional[dict] = None
    actions: Optional[dict] = None

    overall_confidence: int = Field(default=0, ge=0, le=100)
    confidence_note: str = Field(default="")
    agent_status: AgentStatus = Field(default_factory=AgentStatus)
