"""
RootSight — Root Cause Analysis Schemas

Models for RCA hypotheses with confidence scores and evidence.
Produced by the RCA Agent.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class RCAHypothesis(BaseModel):
    """A single root-cause hypothesis with evidence."""
    rank: int = Field(..., ge=1)
    statement: str = Field(..., description="Clear hypothesis statement")
    confidence: int = Field(..., ge=0, le=100, description="Evidence-backed confidence score")
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    plausibility: str = Field(default="", description="Narrative explaining reasoning")


class RCAHypotheses(BaseModel):
    """
    Ranked root-cause hypotheses for the incident.
    Produced by the RCA Agent.
    """
    incident_id: str
    hypotheses: list[RCAHypothesis] = Field(default_factory=list)
    overall_confidence: int = Field(default=0, ge=0, le=100)
    reasoning_note: str = Field(default="", description="Summary note on confidence calibration")
