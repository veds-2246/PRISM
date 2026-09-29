from fastapi import HTTPException, status


def owned_analysis(client, analysis_id: str, user_id: str) -> dict:
    response = client.table("analyses").select("*").eq("id", analysis_id).single().execute()
    row = response.data
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found")
    if str(row.get("user_id")) != str(user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You cannot access this analysis")
    return row


def recommendation_analysis(client, recommendation_id: str, user_id: str) -> tuple[dict, dict]:
    response = client.table("recommendations").select("*").eq("id", recommendation_id).single().execute()
    recommendation = response.data
    if not recommendation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recommendation not found")
    analysis = owned_analysis(client, recommendation["analysis_id"], user_id)
    return recommendation, analysis
