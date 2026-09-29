from fastapi import APIRouter

from app.db.database import supabase

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "sih26108-backend",
    }


@router.get("/health/database")
def database_health_check():
    if supabase is None:
        return {"status": "degraded", "database": "not_configured"}
    try:
        response = supabase.table("product_categories").select("id").limit(1).execute()
        return {"status": "ok", "database": "connected", "sample_count": len(response.data or [])}
    except Exception:
        return {"status": "degraded", "database": "unavailable"}