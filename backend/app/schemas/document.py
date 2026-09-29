from uuid import UUID
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    file_name: str
    mime_type: str | None = None
    file_size: int | None = None
    status: str
    extracted_text: str | None = None
    ocr_used: bool | None = None
    processing_error: str | None = None
