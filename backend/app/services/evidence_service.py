from typing import Any


def insert_recommendation_evidence(
    client: Any,
    recommendation_id: str,
    evidence_type: str,
    evidence_text: str,
    source_document_id: str | None = None,
    source_chunk_id: str | None = None,
    source_standard_id: str | None = None,
    source_url: str | None = None,
) -> Any:
    return client.rpc(
        "insert_recommendation_evidence",
        {
            "p_recommendation_id": recommendation_id,
            "p_evidence_type": evidence_type,
            "p_evidence_text": evidence_text,
            "p_source_document_id": source_document_id,
            "p_source_chunk_id": source_chunk_id,
            "p_source_standard_id": source_standard_id,
            "p_source_url": source_url,
        },
    ).execute()
