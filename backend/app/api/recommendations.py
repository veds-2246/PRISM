from uuid import UUID
from fastapi import APIRouter, Depends
from app.core.security import get_current_user, require_reviewer
from app.db.database import get_supabase_client
from app.schemas.review import ReviewCreate, ReviewResponse
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.access_service import recommendation_analysis
from app.services.audit_service import record_event

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{recommendation_id}/reviews", summary="List recommendation reviews")
def get_reviews(recommendation_id: UUID, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    recommendation_analysis(client, str(recommendation_id), user["id"])
    return client.table("reviews").select("*").eq("recommendation_id", str(recommendation_id)).order("reviewed_at", desc=True).execute().data or []


@router.post("/{recommendation_id}/review", response_model=ReviewResponse, summary="Review a recommendation")
def review(recommendation_id: UUID, data: ReviewCreate, user: dict = Depends(require_reviewer)):
    client = get_supabase_client(user["access_token"])
    recommendation_analysis(client, str(recommendation_id), user["id"])
    row = client.table("reviews").insert({"recommendation_id": str(recommendation_id), "reviewer_id": user["id"], "status": data.status, "comments": data.comments}).execute().data[0]
    client.table("recommendations").update({"review_status": data.status}).eq("id", str(recommendation_id)).execute()
    record_event(client, user["id"], "recommendation_reviewed", "recommendation", str(recommendation_id), {"status": data.status})
    return row


@router.get("/{recommendation_id}/feedback", summary="List recommendation feedback")
def get_feedback(recommendation_id: UUID, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    recommendation_analysis(client, str(recommendation_id), user["id"])
    return client.table("user_feedback").select("*").eq("recommendation_id", str(recommendation_id)).execute().data or []


@router.post("/{recommendation_id}/feedback", response_model=FeedbackResponse, summary="Submit recommendation feedback")
def feedback(recommendation_id: UUID, data: FeedbackCreate, user: dict = Depends(get_current_user)):
    client = get_supabase_client(user["access_token"])
    recommendation_analysis(client, str(recommendation_id), user["id"])
    row = client.table("user_feedback").insert({"recommendation_id": str(recommendation_id), "user_id": user["id"], "feedback_type": data.feedback_type, "comments": data.comments}).execute().data[0]
    record_event(client, user["id"], "feedback_submitted", "recommendation", str(recommendation_id), {"feedback_type": data.feedback_type})
    return row
