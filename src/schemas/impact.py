from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class SeverityBand(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Impact(BaseModel):
    incident_id: str = Field(min_length=1, max_length=64)
    affected_services: list[str] = Field(default_factory=list)
    severity_band: SeverityBand
    estimated_duration_minutes: Optional[int] = Field(default=None, ge=0)
    probable_user_impact: str = Field(min_length=1)
    estimated_requests_affected: Optional[str] = None
    business_impact_summary: Optional[str] = None
