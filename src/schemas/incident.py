from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"

class IncidentStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    INVESTIGATING = "investigating"

class IncidentBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    service: str = Field(min_length=1, max_length=100)
    severity: Severity
    environment: str = Field(default="production", min_length=1, max_length=100)
    region: str = Field(default="us-east-1", min_length=1, max_length=100)
    source: str = Field(default="pagerduty", min_length=1, max_length=100)
    description: Optional[str] = None
    started_at: datetime

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str = Field(index=True, min_length=1, max_length=64)
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: IncidentStatus = IncidentStatus.ACTIVE
