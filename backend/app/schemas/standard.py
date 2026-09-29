from uuid import UUID
from pydantic import BaseModel


class StandardResponse(BaseModel):
    id: UUID
    standard_number: str
    title: str
    description: str | None = None
    scope: str | None = None
    product_category_id: UUID | None = None
    technical_domain: str | None = None
    status: str
    source_name: str | None = None
    source_url: str | None = None
    created_at: str | None = None


class StandardVersionResponse(BaseModel):
    id: UUID
    standard_id: UUID
    version_label: str | None = None
    publication_date: str | None = None
    is_current: bool | None = None
    source_url: str | None = None


class StandardCreate(BaseModel):
    standard_number: str
    title: str
    description: str | None = None
    scope: str | None = None
    product_category_id: UUID | None = None
    technical_domain: str | None = None
    status: str = "active"
    source_name: str | None = None
    source_url: str | None = None
