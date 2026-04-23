from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum


class EventType(str, Enum):
    DEPLOY = "deploy"
    ERROR_SPIKE = "error_spike"
    LATENCY_SPIKE = "latency_spike"
    CPU_SPIKE = "cpu_spike"
    MEMORY_SPIKE = "memory_spike"
    DB_FAILURE = "db_failure"
    TIMEOUT = "timeout"
    FAILOVER = "failover"
    RECOVERY = "recovery"
    ROLLBACK = "rollback"
    DEPENDENCY_FAILURE = "dependency_failure"
    CONFIG_CHANGE = "config_change"
    UNKNOWN = "unknown"


class Event(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    incident_id: str = Field(min_length=1, max_length=64)
    timestamp: datetime
    event_type: EventType
    description: str = Field(min_length=1)
    evidence_source: str = Field(min_length=1)
    confidence: int = Field(ge=0, le=100)
    raw_reference: Optional[str] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v):
        """Handle float-to-int conversion and clamping for confidence scores.

        - If a float in [0.0, 1.0] is received, scale to [0, 100]
        - If out of [0, 100] range, clamp to bounds
        """
        if isinstance(v, float):
            if 0.0 <= v <= 1.0:
                v = int(round(v * 100))
            else:
                v = int(round(v))
        if isinstance(v, (int, float)):
            return max(0, min(100, int(v)))
        return v


class EventList(BaseModel):
    events: list[Event] = Field(default_factory=list)
    timeline_confidence: int = Field(ge=0, le=100, default=0)
    gaps_detected: int = Field(ge=0, default=0)
    total_events: int
    analysis_note: Optional[str] = None
