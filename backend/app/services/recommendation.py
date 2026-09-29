"""Explainable recommendation orchestration built on semantic retrieval.

Ranking uses the retrieved cosine similarity as the relevance score. Extracted
requirement matches are a deterministic tie-breaker only; no unvalidated
weight or confidence score is introduced.
"""

import re
from collections.abc import Iterable
from typing import Any

from app.services.embedding_service import retrieve_standards
from app.services.evidence_service import insert_recommendation_evidence

RECOMMENDATION_TYPES = {
    "primary",
    "related",
    "normative",
    "test",
    "safety",
    "installation",
    "terminology",
}
RELATION_TYPES = {
    "related": "related",
    "normative_reference": "normative",
    "test_method": "test",
    "test": "test",
    "safety": "safety",
    "installation": "installation",
    "terminology": "terminology",
}


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text.lower())}


def _requirement_matches(
    requirements: Iterable[dict[str, Any]],
    candidate: dict[str, Any],
) -> list[str]:
    standard_text = " ".join(
        str(candidate.get(field) or "")
        for field in ("standard_number", "title", "description", "scope", "technical_domain")
    )
    standard_terms = _terms(standard_text)
    return [
        str(requirement.get("requirement_value"))
        for requirement in requirements
        if _terms(str(requirement.get("requirement_value") or "")) & standard_terms
    ]


def _relation_type(
    candidate_id: str,
    relationship_rows: Iterable[dict[str, Any]],
    normative_rows: Iterable[dict[str, Any]],
) -> str:
    for row in _applicable_relationships(candidate_id, relationship_rows):
        mapped = RELATION_TYPES.get(str(row.get("relationship_type") or "").lower())
        if mapped:
            return mapped
    if any(
        str(row.get("referenced_standard_id") or "") == candidate_id
        for row in normative_rows
    ):
        return "normative"
    return "primary"


def _applicable_relationships(
    candidate_id: str,
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep relationship evidence where the candidate is the target endpoint."""
    return [
        row for row in rows
        if str(row.get("target_standard_id") or "") == candidate_id
    ]


def _standard_label(candidate: dict[str, Any]) -> str:
    number = candidate.get("standard_number") or str(candidate.get("standard_id"))
    title = candidate.get("title")
    return f"{number} — {title}" if title else str(number)


def _build_explanation(
    candidate: dict[str, Any],
    requirements: list[dict[str, Any]],
    matched_requirements: list[str],
    relationship_rows: list[dict[str, Any]],
    normative_rows: list[dict[str, Any]],
    certification_rows: list[dict[str, Any]],
    recommendation_type: str,
) -> str:
    parts = [
        "User-provided requirement: "
        + (", ".join(matched_requirements) if matched_requirements else "No extracted requirement text matched the standard metadata."),
        f"Retrieved standard information: {_standard_label(candidate)}.",
        (
            "Current version represented in the database: "
            f"{candidate.get('version_label')}."
            if candidate.get("is_current") and candidate.get("version_label")
            else "No current standard version label was returned."
        ),
        f"Semantic retrieval/ranking result: cosine similarity {float(candidate.get('similarity_score', 0.0)):.4f}.",
        f"System-generated recommendation type: {recommendation_type}.",
    ]
    if relationship_rows:
        parts.append(
            "Database relationship evidence: "
            + ", ".join(str(row.get("relationship_type")) for row in relationship_rows)
            + "."
        )
    if normative_rows:
        parts.append("Database normative-reference evidence: an existing normative reference row was found.")
    if certification_rows:
        parts.append("Database certification evidence: an existing certification requirement row was found.")
    if not requirements:
        parts.insert(0, "User-provided requirement: No extracted requirements were stored for this analysis.")
    return " ".join(parts)


def _fetch_rows(client: Any, table: str, standard_ids: list[str]) -> list[dict[str, Any]]:
    if not standard_ids:
        return []
    if table == "standard_relationships":
        rows: list[dict[str, Any]] = []
        for column in ("source_standard_id", "target_standard_id"):
            rows.extend(
                client.table(table).select("*").in_(column, standard_ids).execute().data or []
            )
        return list({str(row["id"]): row for row in rows if row.get("id")}.values()) + [
            row for row in rows if not row.get("id")
        ]
    if table == "normative_references":
        rows: list[dict[str, Any]] = []
        for column in ("standard_id", "referenced_standard_id"):
            rows.extend(
                client.table(table).select("*").in_(column, standard_ids).execute().data or []
            )
        return list({str(row["id"]): row for row in rows if row.get("id")}.values()) + [
            row for row in rows if not row.get("id")
        ]
    return client.table(table).select("*").in_("standard_id", standard_ids).execute().data or []


def _candidate_evidence(
    candidate: dict[str, Any],
    requirements: list[dict[str, Any]],
    relationship_rows: list[dict[str, Any]],
    normative_rows: list[dict[str, Any]],
    certification_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for requirement in requirements:
        if _terms(str(requirement.get("requirement_value") or "")) & _terms(
            " ".join(str(candidate.get(field) or "") for field in (
                "standard_number", "title", "description", "scope", "technical_domain"
            ))
        ):
            evidence.append({
                "evidence_type": "requirement",
                "evidence_text": f"Extracted requirement: {requirement.get('requirement_value')}",
            })
    if candidate.get("standard_number") or candidate.get("title"):
        evidence.append({
            "evidence_type": "standard",
            "evidence_text": f"Retrieved standard: {_standard_label(candidate)}.",
            "source_standard_id": candidate["standard_id"],
        })
    for row in relationship_rows:
        evidence.append({
            "evidence_type": "relationship",
            "evidence_text": f"Existing standard relationship: {row.get('relationship_type')}.",
            "source_standard_id": candidate["standard_id"],
        })
    for row in normative_rows:
        evidence.append({
            "evidence_type": "normative",
            "evidence_text": "Existing normative reference record for this standard.",
            "source_standard_id": candidate["standard_id"],
        })
    for row in certification_rows:
        details = row.get("description") or row.get("certification_name") or "Existing certification requirement."
        evidence.append({
            "evidence_type": "certification",
            "evidence_text": f"Existing certification requirement: {details}.",
            "source_standard_id": candidate["standard_id"],
        })
    return evidence


def _persist_evidence(client: Any, recommendation_id: str, evidence: list[dict[str, Any]]) -> None:
    existing = client.table("recommendation_evidence").select(
        "evidence_type,evidence_text,source_standard_id,source_document_id,source_chunk_id"
    ).eq("recommendation_id", recommendation_id).execute().data or []
    existing_keys = {
        (
            row.get("evidence_type"),
            row.get("evidence_text"),
            row.get("source_standard_id"),
            row.get("source_document_id"),
            row.get("source_chunk_id"),
        )
        for row in existing
    }
    for item in evidence:
        key = (
            item.get("evidence_type"),
            item.get("evidence_text"),
            item.get("source_standard_id"),
            item.get("source_document_id"),
            item.get("source_chunk_id"),
        )
        if key not in existing_keys:
            insert_recommendation_evidence(
                client,
                recommendation_id=recommendation_id,
                evidence_type=item["evidence_type"],
                evidence_text=item["evidence_text"],
                source_standard_id=item.get("source_standard_id"),
            )
            existing_keys.add(key)


def _existing_recommendation(
    client: Any,
    analysis_id: str,
    candidate: dict[str, Any],
    recommendation_type: str,
) -> dict[str, Any] | None:
    query = client.table("recommendations").select("*").eq(
        "analysis_id", analysis_id
    ).eq("standard_id", str(candidate["standard_id"])).eq(
        "recommendation_type", recommendation_type
    )
    version_id = candidate.get("standard_version_id")
    query = query.eq("standard_version_id", str(version_id)) if version_id else query.is_(
        "standard_version_id", "null"
    )
    return (query.limit(1).execute().data or [None])[0]


def generate_recommendations(
    client: Any,
    analysis_id: str,
    query_text: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Rank only semantic candidates and persist explainable recommendations."""
    requirements = client.table("extracted_requirements").select("*").eq(
        "analysis_id", analysis_id
    ).execute().data or []
    candidates = retrieve_standards(client, query_text, top_k)
    standard_ids = [str(candidate["standard_id"]) for candidate in candidates]
    relationship_rows = _fetch_rows(client, "standard_relationships", standard_ids)
    normative_rows = _fetch_rows(client, "normative_references", standard_ids)
    certification_rows = _fetch_rows(client, "certification_requirements", standard_ids)

    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        standard_id = str(candidate["standard_id"])
        candidate_relationships = _applicable_relationships(standard_id, relationship_rows)
        candidate_normative = [
            row for row in normative_rows
            if str(row.get("referenced_standard_id") or "") == standard_id
        ]
        candidate_certification = [
            row for row in certification_rows if str(row.get("standard_id")) == standard_id
        ]
        recommendation_type = _relation_type(
            standard_id, candidate_relationships, candidate_normative
        )
        if recommendation_type not in RECOMMENDATION_TYPES:
            raise ValueError(f"Unsupported recommendation type: {recommendation_type}")
        matched_requirements = _requirement_matches(requirements, candidate)
        ranked.append({
            **candidate,
            "recommendation_type": recommendation_type,
            "matched_requirements": matched_requirements,
            "relationship_rows": candidate_relationships,
            "normative_rows": candidate_normative,
            "certification_rows": candidate_certification,
        })

    ranked.sort(
        key=lambda candidate: (
            -float(candidate.get("similarity_score", 0.0)),
            -len(candidate["matched_requirements"]),
            str(candidate.get("standard_number") or ""),
        )
    )
    persisted: list[dict[str, Any]] = []
    for rank, candidate in enumerate(ranked, 1):
        evidence = _candidate_evidence(
            candidate,
            requirements,
            candidate["relationship_rows"],
            candidate["normative_rows"],
            candidate["certification_rows"],
        )
        explanation = _build_explanation(
            candidate,
            requirements,
            candidate["matched_requirements"],
            candidate["relationship_rows"],
            candidate["normative_rows"],
            candidate["certification_rows"],
            candidate["recommendation_type"],
        )
        existing = _existing_recommendation(
            client, analysis_id, candidate, candidate["recommendation_type"]
        )
        payload = {
            "analysis_id": analysis_id,
            "standard_id": candidate["standard_id"],
            "standard_version_id": candidate.get("standard_version_id"),
            "recommendation_type": candidate["recommendation_type"],
            "rank": rank,
            "relevance_score": round(float(candidate.get("similarity_score", 0.0)), 4),
            "confidence_score": None,
            "explanation": explanation,
            "review_status": "pending",
        }
        if existing:
            recommendation_id = str(existing["id"])
            update_payload = {key: value for key, value in payload.items() if key != "review_status"}
            client.table("recommendations").update(update_payload).eq("id", recommendation_id).execute()
            persisted.append({**existing, **update_payload})
        else:
            inserted = client.table("recommendations").insert(payload).execute().data or []
            if not inserted:
                raise RuntimeError("Unable to persist recommendation")
            recommendation_id = str(inserted[0]["id"])
            persisted.append(inserted[0])
        if evidence:
            _persist_evidence(client, recommendation_id, evidence)
    return persisted
