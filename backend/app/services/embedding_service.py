"""Lightweight 768-dimensional embeddings for the serverless deployment."""

from collections.abc import Sequence
from typing import Any
import hashlib
import math
import re

from app.core.config import settings

EMBEDDING_DIMENSION = 768
STANDARD_RETRIEVAL_RPC = "match_standard_embeddings"
E5_PASSAGE_PREFIX = "passage: "
E5_QUERY_PREFIX = "query: "


def _hash_embedding(text: str) -> list[float]:
    """Create a deterministic normalized 768-d vector without ML packages."""
    vector = [0.0] * EMBEDDING_DIMENSION
    tokens = re.findall(r"[\w]+", text.lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSION
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


class EmbeddingService:
    """Small deterministic embedding adapter for Vercel/serverless use."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or "prism-hash-768"

    @property
    def available(self) -> bool:
        return True

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return [_hash_embedding(f"{E5_PASSAGE_PREFIX}{text}") for text in texts]

    def encode_queries(self, texts: Sequence[str]) -> list[list[float]]:
        return [_hash_embedding(f"{E5_QUERY_PREFIX}{text}") for text in texts]


def build_standard_passage(standard: dict[str, Any]) -> str:
    fields = (
        ("Standard number", standard.get("standard_number")),
        ("Title", standard.get("title")),
        ("Description", standard.get("description")),
        ("Scope", standard.get("scope")),
        ("Technical domain", standard.get("technical_domain")),
    )
    return "\n".join(f"{label}: {value}" for label, value in fields if value)


def standard_embedding_payload(standard: dict[str, Any], embedding: list[float], standard_version_id: str | None = None) -> dict[str, Any]:
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError("Standard embedding payload must contain 768 values")
    return {"standard_id": standard["id"], "standard_version_id": standard_version_id, "content": build_standard_passage(standard), "embedding": embedding, "embedding_model": settings.embedding_model}


def document_chunk_embedding_payload(chunk: dict[str, Any], embedding: list[float]) -> dict[str, Any]:
    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError("Document chunk embedding payload must contain 768 values")
    return {"document_chunk_id": chunk["id"], "content": chunk["content"], "embedding": embedding, "embedding_model": settings.embedding_model}


def persist_embeddings(client: Any, payloads: Sequence[dict[str, Any]]) -> int:
    inserted = 0
    for payload in payloads:
        query = client.table("embeddings").select("id").eq("embedding_model", payload["embedding_model"])
        if payload.get("document_chunk_id"):
            query = query.eq("document_chunk_id", payload["document_chunk_id"])
        else:
            query = query.eq("standard_id", payload["standard_id"])
            version_id = payload.get("standard_version_id")
            query = query.eq("standard_version_id", version_id) if version_id else query.is_("standard_version_id", "null")
        if query.limit(1).execute().data:
            continue
        response = client.table("embeddings").insert(payload).execute()
        if not response.data:
            raise RuntimeError("Embedding persistence returned no inserted row")
        inserted += 1
    return inserted


def index_standards(client: Any | None = None) -> int:
    if client is None:
        from app.db.database import get_trusted_supabase_client
        client = get_trusted_supabase_client()
    standards = client.table("standards").select("id,standard_number,title,description,scope,technical_domain").execute().data or []
    standard_ids = [row["id"] for row in standards]
    versions = (client.table("standard_versions").select("id,standard_id").in_("standard_id", standard_ids).eq("is_current", True).execute().data or []) if standard_ids else []
    version_by_standard = {str(row["standard_id"]): row["id"] for row in versions}
    service = EmbeddingService()
    embeddings = service.encode([build_standard_passage(row) for row in standards])
    payloads = [standard_embedding_payload(standard, embedding, version_by_standard.get(str(standard["id"]))) for standard, embedding in zip(standards, embeddings, strict=True)]
    return persist_embeddings(client, payloads)


def index_document_chunks(client: Any, chunks: Sequence[dict[str, Any]]) -> int:
    if not chunks:
        return 0
    embeddings = EmbeddingService().encode([str(chunk["content"]) for chunk in chunks])
    payloads = [document_chunk_embedding_payload(chunk, embedding) for chunk, embedding in zip(chunks, embeddings, strict=True)]
    return persist_embeddings(client, payloads)


def retrieve_standards(client: Any, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Query must not be empty")
    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")
    query_embedding = EmbeddingService().encode_queries([normalized_query])[0]
    response = client.rpc(STANDARD_RETRIEVAL_RPC, {"query_embedding": query_embedding, "match_count": top_k, "p_embedding_model": settings.embedding_model}).execute()
    matches = response.data or []
    if not matches:
        return []
    standard_ids = [str(row["standard_id"]) for row in matches if row.get("standard_id")]
    version_ids = [str(row["standard_version_id"]) for row in matches if row.get("standard_version_id")]
    standards = client.table("standards").select("id,standard_number,title,description,scope,technical_domain,status").in_("id", standard_ids).execute().data or []
    versions = client.table("standard_versions").select("id,version_label,is_current,publication_date,revision_date").in_("id", version_ids).execute().data or []
    standards_by_id = {str(row["id"]): row for row in standards}
    versions_by_id = {str(row["id"]): row for row in versions}
    results: list[dict[str, Any]] = []
    for match in matches:
        standard_id = match.get("standard_id")
        if not standard_id:
            continue
        standard = standards_by_id.get(str(standard_id), {})
        version_id = match.get("standard_version_id")
        version = versions_by_id.get(str(version_id), {}) if version_id else {}
        raw_similarity = float(match.get("similarity_score", match.get("similarity", 0)))
        similarity = raw_similarity if 0.0 <= raw_similarity <= 1.0 else (raw_similarity + 1.0) / 2.0
        results.append({"standard_id": standard_id, "standard_version_id": version_id, "standard_number": standard.get("standard_number"), "title": standard.get("title"), "description": standard.get("description"), "scope": standard.get("scope"), "technical_domain": standard.get("technical_domain"), "status": standard.get("status"), "version_label": version.get("version_label"), "is_current": version.get("is_current"), "publication_date": version.get("publication_date"), "revision_date": version.get("revision_date"), "similarity_score": min(1.0, max(0.0, similarity)), "embedding_model": settings.embedding_model})
    return sorted(results, key=lambda row: row["similarity_score"], reverse=True)
