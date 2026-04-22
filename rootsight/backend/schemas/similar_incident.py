from pydantic import BaseModel, Field

class SimilarIncident(BaseModel):
    incident_id: str = Field(min_length=1, max_length=64)
    similar_to_id: str = Field(min_length=1, max_length=64)
    similarity_score: float = Field(ge=0.0, le=1.0)
    why_similar: str = Field(min_length=1)
    previous_fix: str = Field(min_length=1)

class SimilarIncidentList(BaseModel):
    matches: list[SimilarIncident] = Field(default_factory=list)
