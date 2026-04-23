from pydantic import BaseModel, Field, field_validator
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
    severity_band: Optional[str] = Field(default=None, description="Severity override for low-confidence hypotheses")

    @field_validator("severity_band", mode="after")
    @classmethod
    def override_low_confidence_severity(cls, v, info):
        """Force severity_band to 'low' for hypotheses with confidence < 30."""
        confidence = info.data.get("confidence_score", 100)
        if confidence < 30:
            return "low"
        return v


class HypothesisList(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    analysis_confidence: int = Field(ge=0, le=100, default=0)
    is_low_confidence: bool = False
    analysis_note: Optional[str] = None
