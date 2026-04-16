"""
RootSight — Timeline Schemas

Models for timeline events and the complete incident timeline.
Produced by the Timeline Agent.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """A single meaningful event extracted from logs."""
    timestamp: str = Field(..., description="ISO-8601 event timestamp")
    event_type: str = Field(..., description="deploy, error_spike, latency_spike, config_change, recovery, alert, etc.")
    description: str = Field(..., description="Human-readable event description")
    evidence_source: str = Field(default="application logs", description="Where the evidence came from")
    severity: str = Field(default="info", description="info, warning, high, critical")


class IncidentTimeline(BaseModel):
    """
    Chronological timeline of the incident.
    Produced by the Timeline Agent.
    """
    incident_id: str
    events: list[TimelineEvent] = Field(default_factory=list)
    timeline_confidence: int = Field(default=0, ge=0, le=100, description="Confidence in timeline completeness")
    gaps: list[str] = Field(default_factory=list, description="Known gaps or uncertainties in the timeline")
