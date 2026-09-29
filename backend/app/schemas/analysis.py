from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisCreate(BaseModel):
    query_text: str = Field(..., min_length=1)
    product_name: str | None = None
    product_category_id: UUID | None = None
    technical_specifications: str | None = None
    defer_processing: bool = False


class AnalysisResponse(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID | None
    query_text: str | None
    status: str
    detected_language: str | None
    product_name: str | None
    product_category_id: UUID | None
    error_message: str | None = None
