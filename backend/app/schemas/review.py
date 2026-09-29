from uuid import UUID
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    status: str = Field(pattern="^(pending|accepted|rejected|needs_review)$")
    comments: str | None = None


class ReviewResponse(BaseModel):
    id: UUID
    recommendation_id: UUID
    reviewer_id: UUID
    status: str
    comments: str | None = None
    reviewed_at: str | None = None
