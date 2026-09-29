from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.security import get_current_user
from app.db.database import get_supabase_client
from app.schemas.standard import StandardResponse, StandardVersionResponse
from app.services.embedding_service import retrieve_standards

router = APIRouter(prefix="/standards", tags=["Standards"])


def _client(user: dict):
    return get_supabase_client(user["access_token"])


@router.get("", response_model=list[StandardResponse], summary="List and filter standards")
@router.get("/search", summary="Search standards")
def get_standards(
    search: str | None = Query(None),
    q: str | None = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    product_category_id: UUID | None = Query(None),
    technical_domain: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    client = _client(user)
    if q is not None:
        if not q.strip():
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "q must not be empty")
        return retrieve_standards(client, q, top_k)
    query = client.table("standards").select("*").limit(limit)
    if search:
        safe = search.replace(",", " ")
        query = query.or_(f"standard_number.ilike.%{safe}%,title.ilike.%{safe}%,description.ilike.%{safe}%,scope.ilike.%{safe}%")
    if product_category_id:
        query = query.eq("product_category_id", str(product_category_id))
    if technical_domain:
        query = query.ilike("technical_domain", f"%{technical_domain}%")
    return query.execute().data or []


@router.get("/{standard_id}", response_model=StandardResponse, summary="Get standard details")
def get_standard(standard_id: UUID, user: dict = Depends(get_current_user)):
    return _client(user).table("standards").select("*").eq("id", str(standard_id)).single().execute().data


@router.get("/{standard_id}/versions", response_model=list[StandardVersionResponse], summary="List standard versions")
def versions(standard_id: UUID, user: dict = Depends(get_current_user)):
    return _client(user).table("standard_versions").select("*").eq("standard_id", str(standard_id)).execute().data or []


@router.get("/{standard_id}/amendments", summary="List standard amendments")
def amendments(
    standard_id: UUID,
    user: dict = Depends(get_current_user),
):
    client = _client(user)

    versions = (
        client.table("standard_versions")
        .select("id")
        .eq("standard_id", str(standard_id))
        .execute()
        .data
        or []
    )

    version_ids = [version["id"] for version in versions]

    if not version_ids:
        return []

    return (
        client.table("amendments")
        .select("*")
        .in_("standard_version_id", version_ids)
        .execute()
        .data
        or []
    )

@router.get("/{standard_id}/relationships", summary="List related standards")
def relationships(standard_id: UUID, user: dict = Depends(get_current_user)):
    client = _client(user)
    standard_id_value = str(standard_id)
    source_rows = (
        client.table("standard_relationships")
        .select("*")
        .eq("source_standard_id", standard_id_value)
        .execute()
        .data
        or []
    )
    target_rows = (
        client.table("standard_relationships")
        .select("*")
        .eq("target_standard_id", standard_id_value)
        .execute()
        .data
        or []
    )
    rows_by_id = {str(row["id"]): row for row in source_rows + target_rows if row.get("id")}
    rows_without_id = [
        row for row in source_rows + target_rows
        if not row.get("id") and row not in rows_by_id.values()
    ]
    return list(rows_by_id.values()) + rows_without_id


@router.get("/{standard_id}/normative-references", summary="List normative references")
def normative_references(standard_id: UUID, user: dict = Depends(get_current_user)):
    return _client(user).table("normative_references").select("*").eq("standard_id", str(standard_id)).execute().data or []


@router.get("/{standard_id}/certification", summary="List certification requirements")
def certification(standard_id: UUID, user: dict = Depends(get_current_user)):
    return _client(user).table("certification_requirements").select("*").eq("standard_id", str(standard_id)).execute().data or []
