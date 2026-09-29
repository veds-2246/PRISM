from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import require_admin
from app.db.database import get_supabase_client
from app.schemas.standard import StandardCreate, StandardResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", summary="List organization profiles")
def users(user: dict = Depends(require_admin)):
    return get_supabase_client(user["access_token"]).table("profiles").select("id,organization_id,full_name,created_at").execute().data or []


@router.get("/standards", summary="List standards for administration")
def standards(user: dict = Depends(require_admin)):
    return get_supabase_client(user["access_token"]).table("standards").select("*").execute().data or []


@router.post("/standards", response_model=StandardResponse, status_code=201, summary="Create a standard")
def create_standard(data: StandardCreate, user: dict = Depends(require_admin)):
    payload = data.model_dump(exclude_none=True)
    response = get_supabase_client(user["access_token"]).table("standards").insert(payload).execute()
    if not response.data:
        raise HTTPException(500, "Unable to create standard")
    return response.data[0]


@router.patch("/standards/{standard_id}", response_model=StandardResponse, summary="Update a standard")
def update_standard(standard_id: UUID, data: dict, user: dict = Depends(require_admin)):
    allowed = {"standard_number", "title", "description", "scope", "product_category_id", "technical_domain", "status", "source_name", "source_url"}
    payload = {key: value for key, value in data.items() if key in allowed}
    response = get_supabase_client(user["access_token"]).table("standards").update(payload).eq("id", str(standard_id)).execute()
    if not response.data:
        raise HTTPException(404, "Standard not found")
    return response.data[0]
