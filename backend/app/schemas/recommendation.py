from uuid import UUID
from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    standard_id: UUID
    standard_version_id: UUID | None = None
    recommendation_type: str
    rank: int
    relevance_score: float
    confidence_score: float | None = None
    explanation: str | None = None
    review_status: str
    standard: dict | None = None
    evidence: list[dict] = []
