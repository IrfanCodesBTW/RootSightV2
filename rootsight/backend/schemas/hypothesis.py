from pydantic import BaseModel, Field
from typing import Optional

class Hypothesis(BaseModel):
    hypothesis_id: str = Field(min_length=1, max_length=64)
    incident_id: str = Field(min_length=1, max_length=64)
    rank: int = Field(ge=1)
    statement: str = Field(min_length=1)
    confidence_score: int = Field(ge=0, le=100)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_check: Optional[str] = None

class HypothesisList(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    analysis_confidence: int = Field(ge=0, le=100, default=0)
    is_low_confidence: bool = False
    analysis_note: Optional[str] = None
