from pydantic import BaseModel, Field, model_validator
from typing import Literal, List, Optional

class Hypothesis(BaseModel):
    id: str = Field(..., description="Unique identifier for the hypothesis (e.g., 'H1')")
    text: str = Field(..., description="Clear, concise description of the hypothesized root cause.")
    supporting_event_ids: List[str] = Field(..., min_length=1, description="List of specific event IDs from the EventList that support this hypothesis.")
    evidence_strength: Literal["strong", "moderate", "weak"] = Field(
        default="weak",
        description="Strength of the supporting evidence: 'strong' (3+ correlated events), 'moderate' (2 events), 'weak' (1 event).",
    )
    confidence: Literal["low", "medium", "high"] = Field(..., description="Categorical confidence level of the hypothesis.")
    category: Literal["infrastructure", "application", "dependency", "configuration"] = Field(..., description="The architectural domain of the root cause.")
    recommended_action_hint: str = Field(..., description="Brief next step to verify or mitigate this cause.")

class HypothesisList(BaseModel):
    hypotheses: List[Hypothesis] = Field(default_factory=list, max_length=3, description="List of hypotheses, ranked by confidence descending. Maximum of 3.")
    insufficient_data: bool = Field(..., description="True if fewer than 3 events were provided or data is too sparse to conclude.")

    @model_validator(mode='after')
    def enforce_rejection_rule(self):
        if self.insufficient_data and len(self.hypotheses) > 0:
            raise ValueError("Rejection Rule Violation: If 'insufficient_data' is true, 'hypotheses' must be empty.")
        
        confidence_weights = {"high": 3, "medium": 2, "low": 1}
        for i in range(len(self.hypotheses) - 1):
            current_weight = confidence_weights[self.hypotheses[i].confidence]
            next_weight = confidence_weights[self.hypotheses[i+1].confidence]
            if current_weight < next_weight:
                self.hypotheses.sort(key=lambda h: confidence_weights[h.confidence], reverse=True)
                break 

        return self
