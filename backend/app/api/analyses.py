from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.database import get_supabase_client
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.services.access_service import owned_analysis
from app.services.analysis_service import complete_analysis
from app.utils.language import detect_language

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED,
             summary="Create an analysis and generate recommendations")
def create_analysis(data: AnalysisCreate, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    profile = client.table("profiles").select("organization_id").eq("id", user["id"]).single().execute().data
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User profile not found")
    input_text = " ".join(filter(None, [data.query_text, data.product_name, data.technical_specifications]))
    row = client.table("analyses").insert({
        "user_id": user["id"], "organization_id": profile.get("organization_id"),
        "query_text": input_text, "product_name": data.product_name,
        "product_category_id": str(data.product_category_id) if data.product_category_id else None,
        "status": "processing", "detected_language": detect_language(data.query_text),
    }).execute().data
    if not row:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Unable to create analysis")
    analysis = row[0]
    if data.defer_processing:
        return analysis
    return complete_analysis(
        client,
        user["access_token"],
        user["id"],
        analysis,
        input_text,
        str(data.product_category_id) if data.product_category_id else None,
    )


@router.get("", response_model=list[AnalysisResponse], summary="List the current user's analyses")
def list_analyses(user: dict = Depends(get_current_user)):
    return get_supabase_client(user["access_token"]).table("analyses").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute().data or []


@router.get("/{analysis_id}", response_model=AnalysisResponse, summary="Get an analysis")
def get_analysis(analysis_id: UUID, user: dict = Depends(get_current_user)):
    return owned_analysis(get_supabase_client(user["access_token"]), str(analysis_id), user["id"])


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an analysis")
def delete_analysis(analysis_id: UUID, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    owned_analysis(client, str(analysis_id), user["id"])
    client.table("analyses").delete().eq("id", str(analysis_id)).execute()


@router.get("/{analysis_id}/report", summary="Return an analysis report")
def analysis_report(analysis_id: UUID, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    analysis = owned_analysis(client, str(analysis_id), user["id"])
    recommendations = client.table("recommendations").select("*").eq("analysis_id", str(analysis_id)).order("rank").execute().data or []
    standard_ids = [str(item["standard_id"]) for item in recommendations if item.get("standard_id")]
    standards = (
        client.table("standards")
        .select("*")
        .in_("id", standard_ids)
        .execute()
        .data
        if standard_ids
        else []
    ) or []
    standards_by_id = {str(row["id"]): row for row in standards}
    version_ids = [str(item["standard_version_id"]) for item in recommendations if item.get("standard_version_id")]
    versions = (
        client.table("standard_versions")
        .select("*")
        .in_("id", version_ids)
        .execute()
        .data
        if version_ids
        else []
    ) or []
    versions_by_id = {str(row["id"]): row for row in versions}
    for item in recommendations:
        item["standard"] = standards_by_id.get(str(item.get("standard_id")))
        item["standard_version"] = versions_by_id.get(str(item.get("standard_version_id")))
    recommendation_ids = [str(item["id"]) for item in recommendations]
    evidence = (
        client.table("recommendation_evidence")
        .select("id, recommendation_id, evidence_type, evidence_text, source_document_id, source_chunk_id, source_standard_id, source_url")
        .in_("recommendation_id", recommendation_ids)
        .execute()
        .data
        if recommendation_ids
        else []
    ) or []
    evidence_by_recommendation_id: dict[str, list[dict]] = {}
    for row in evidence:
        evidence_by_recommendation_id.setdefault(str(row["recommendation_id"]), []).append(row)
    for item in recommendations:
        item["evidence"] = evidence_by_recommendation_id.get(str(item["id"]), [])
        item["reviews"] = client.table("reviews").select("*").eq("recommendation_id", item["id"]).execute().data or []
        item["feedback"] = client.table("user_feedback").select("*").eq("recommendation_id", item["id"]).execute().data or []
    requirements = client.table("extracted_requirements").select("*").eq("analysis_id", str(analysis_id)).execute().data or []
    for requirement in requirements:
        requirement.setdefault("requirement_text", requirement.get("requirement_value"))
    documents = client.table("uploaded_documents").select(
        "id, analysis_id, file_name, file_type, status, file_size, extracted_text, ocr_used, processing_error"
    ).eq("analysis_id", str(analysis_id)).execute().data or []
    for document in documents:
        document["mime_type"] = document.pop("file_type", None)
    return {
        "analysis": analysis,
        "requirements": requirements,
        "recommendations": recommendations,
        "documents": documents,
    }
