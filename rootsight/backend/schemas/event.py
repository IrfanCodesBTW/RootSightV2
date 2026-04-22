from pydantic import BaseModel, Field
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

class EventList(BaseModel):
    events: list[Event] = Field(default_factory=list)
    timeline_confidence: int = Field(ge=0, le=100, default=0)
    gaps_detected: int = Field(ge=0, default=0)
    total_events: int
    analysis_note: Optional[str] = None
