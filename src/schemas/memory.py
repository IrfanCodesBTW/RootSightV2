"""
RootSight — Memory / Similar Incidents Schemas

Models for historical incident matches via vector similarity.
Produced by the Memory Agent.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class SimilarIncident(BaseModel):
    """A single similar incident match from the vector store."""
    matched_incident_id: str
    title: str = Field(default="")
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    similarity_reason: str = Field(default="")
    previous_root_cause: str = Field(default="")
    previous_resolution: str = Field(default="")
    pattern_applies: bool = Field(default=False)


class SimilarIncidents(BaseModel):
    """
    Similar past incident matches.
    Produced by the Memory Agent.
    """
    incident_id: str
    matches: list[SimilarIncident] = Field(default_factory=list)
    no_match_message: Optional[str] = Field(default=None, description="Set when no strong match found")
