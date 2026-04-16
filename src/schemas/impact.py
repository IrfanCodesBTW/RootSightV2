"""
RootSight — Impact Assessment Schemas

Models for severity, blast radius, user and business impact.
Produced by the Impact Agent.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class UserImpact(BaseModel):
    """Estimated user-facing impact."""
    estimate: str = Field(default="qualitative", description="qualitative or quantitative")
    description: str = Field(default="")
    confidence: int = Field(default=0, ge=0, le=100)
    data_limitation: str = Field(default="", description="What data is missing for better estimation")


class BusinessImpact(BaseModel):
    """Estimated business impact."""
    description: str = Field(default="")
    blast_radius: str = Field(default="", description="Which systems/paths are affected")


class ImpactAssessment(BaseModel):
    """
    Full impact assessment for the incident.
    Produced by the Impact Agent.
    """
    incident_id: str
    affected_services: list[str] = Field(default_factory=list)
    severity: str = Field(default="P3", description="P1, P2, P3, or P4")
    estimated_duration_minutes: int = Field(default=0)
    detection_to_response_minutes: int = Field(default=0)
    user_impact: UserImpact = Field(default_factory=UserImpact)
    business_impact: BusinessImpact = Field(default_factory=BusinessImpact)
