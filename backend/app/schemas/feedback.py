from uuid import UUID
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    feedback_type: str = Field(pattern="^(correct|incorrect|not_applicable|missing_standard|needs_further_review)$")
    comments: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    recommendation_id: UUID
    user_id: UUID
    feedback_type: str
    comments: str | None = None
