from typing import Any

from app.services.audit_service import record_event
from app.services.recommendation import generate_recommendations
from app.services.requirement_service import persist_requirements


def complete_analysis(
    client: Any,
    access_token: str,
    user_id: str,
    analysis: dict[str, Any],
    input_text: str,
    category_id: str | None = None,
) -> dict[str, Any]:
    try:
        persist_requirements(client, str(analysis["id"]), input_text)
        recommendations = generate_recommendations(
            client, str(analysis["id"]), input_text
        )
        updated = client.table("analyses").update({
            "status": "completed", "error_message": None,
        }).eq("id", analysis["id"]).execute().data
        record_event(client, user_id, "analysis_completed", "analysis", analysis["id"], {
            "recommendation_count": len(recommendations),
        })
        return updated[0] if updated else {**analysis, "status": "completed"}
    except Exception as exc:
        client.table("analyses").update({
            "status": "failed", "error_message": str(exc)[:500],
        }).eq("id", analysis["id"]).execute()
        record_event(client, user_id, "analysis_failed", "analysis", analysis["id"])
        raise
