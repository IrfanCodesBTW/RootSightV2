from pydantic import BaseModel, Field, field_validator
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
    affected_users: int = Field(default=0, ge=0)
    severity_band: SeverityBand
    estimated_duration_minutes: Optional[int] = Field(default=None, ge=0)
    probable_user_impact: str = Field(min_length=1)
    estimated_requests_affected: Optional[str] = None
    business_impact_summary: Optional[str] = None

    @field_validator("affected_services", mode="before")
    @classmethod
    def ensure_services_list(cls, v):
        """Ensure affected_services is always a list, never None."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("affected_users", mode="before")
    @classmethod
    def ensure_non_negative_users(cls, v):
        """Ensure affected_users is a non-negative integer."""
        if v is None:
            return 0
        v = int(v)
        return max(0, v)
