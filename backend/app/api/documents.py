from pathlib import PurePath
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_supabase_client, get_trusted_supabase_client
from app.schemas.document import DocumentResponse
from app.services.access_service import owned_analysis
from app.services.analysis_service import complete_analysis
from app.services.audit_service import record_event
from app.services.extraction_service import chunk_text, extract_text
from app.services.embedding_service import index_document_chunks

router = APIRouter(prefix="/analyses", tags=["Documents"])
ALLOWED = {".pdf": "application/pdf", ".txt": "text/plain", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@router.post("/{analysis_id}/documents", response_model=DocumentResponse, status_code=201, summary="Upload and process a document")
async def upload_document(analysis_id: UUID, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    analysis = owned_analysis(client, str(analysis_id), user["id"])
    suffix = PurePath(file.filename or "").suffix.lower()
    if suffix not in ALLOWED or file.content_type not in {ALLOWED[suffix], "application/octet-stream"}:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF, TXT, and DOCX files are supported")
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds configured size limit")
    row = client.rpc(
        "insert_uploaded_document",
        {
            "p_analysis_id": str(analysis_id),
            "p_file_name": file.filename or "uploaded-document",
            "p_file_type": file.content_type,
            "p_file_size": len(content),
        },
    ).execute().data or []
    if not row:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unable to create document record")
    document = row[0]
    try:
        extracted = extract_text(content, suffix)
        chunks = chunk_text(extracted.text, pages=extracted.pages)
        stored_chunks = []
        if chunks:
            for chunk in chunks:
                inserted_chunk = client.rpc(
                    "insert_document_chunk",
                    {
                        "p_document_id": document["id"],
                        "p_chunk_index": chunk["chunk_index"],
                        "p_content": chunk["content"],
                        "p_page_number": chunk.get("page_number"),
                        "p_token_count": None,
                    },
                ).execute().data or []
                if not inserted_chunk:
                    raise RuntimeError("Unable to create document chunk")
                stored_chunks.extend(inserted_chunk)
        index_document_chunks(get_trusted_supabase_client(), stored_chunks)
        client.rpc(
            "update_uploaded_document_status",
            {
                "p_document_id": document["id"],
                "p_status": "processed",
                "p_extracted_text": extracted.text,
                "p_ocr_used": extracted.ocr_used,
                "p_ocr_confidence": extracted.ocr_confidence,
                "p_processing_error": None,
            },
        ).execute()
        combined_input = " ".join(filter(None, [analysis.get("query_text"), extracted.text]))
        updated_analysis = client.table("analyses").update({
            "query_text": combined_input,
        }).eq("id", str(analysis_id)).execute().data
        complete_analysis(
            client,
            user["access_token"],
            user["id"],
            updated_analysis[0] if updated_analysis else {**analysis, "query_text": combined_input},
            combined_input,
            str(analysis.get("product_category_id")) if analysis.get("product_category_id") else None,
        )
        record_event(client, user["id"], "document_processed", "uploaded_document", document["id"])
        return {
            **document,
            "status": "processed",
            "mime_type": document.get("file_type"),
            "extracted_text": extracted.text,
            "ocr_used": extracted.ocr_used,
        }
    except Exception as exc:
        client.rpc(
            "update_uploaded_document_status",
            {
                "p_document_id": document["id"],
                "p_status": "failed",
                "p_processing_error": str(exc)[:500],
            },
        ).execute()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
