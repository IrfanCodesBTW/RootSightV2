"""
RootSight — Log Schemas

Models for normalized log entries, log sets, and data quality metrics.
Produced by the Log Agent.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class DataQuality(BaseModel):
    """Quality assessment of ingested log data."""
    completeness: str = Field(default="unknown", description="high | medium | low | unknown")
    noise_level: str = Field(default="unknown", description="high | medium | low")
    deploy_markers_found: bool = Field(default=False)
    confidence_impact: str = Field(default="none", description="none | minor | significant")


class NormalizedLogEntry(BaseModel):
    """A single normalized log entry."""
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    level: str = Field(..., description="Log level: ERROR, WARN, INFO, DEBUG")
    service: str = Field(..., description="Originating service name")
    message: str = Field(..., description="Log message content")
    metadata: dict = Field(default_factory=dict, description="Additional fields: trace_id, host, etc.")


class NormalizedLogSet(BaseModel):
    """
    Complete set of normalized, filtered logs for an incident.
    Produced by the Log Agent.
    """
    incident_id: str
    source: str = Field(default="datadog")
    time_window: dict = Field(default_factory=dict, description="start and end ISO-8601 timestamps")
    total_raw_count: int = Field(default=0, description="Total logs before filtering")
    filtered_count: int = Field(default=0, description="Logs after noise removal")
    data_quality: DataQuality = Field(default_factory=DataQuality)
    logs: list[NormalizedLogEntry] = Field(default_factory=list)
