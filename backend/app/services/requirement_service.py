"""Transparent MVP extraction of procurement requirements."""

from typing import Any


RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("product", ("bar", "wire", "steel", "deformed"), "High strength deformed steel bars and wires"),
    ("application", ("reinforced concrete", "construction", "rcc"), "Reinforced concrete construction"),
    ("mechanical_properties", ("strength", "yield", "tensile", "elongation", "mechanical"), "Mechanical properties"),
    ("dimensions", ("diameter", "dimension", "size", "mm", "length"), "Dimensions"),
    ("chemical_composition", ("chemical", "carbon", "manganese", "composition"), "Chemical composition"),
    ("testing", ("test", "testing", "sample", "inspection"), "Testing requirements"),
    ("standard_compliance", ("bis", "indian standard", "is ", "standard", "compliance"), "BIS/Indian Standard compliance"),
    ("certification", ("certification", "certified", "license", "mark"), "Certification requirements"),
)


def extract_requirements(text: str) -> list[dict[str, str]]:
    normalized = " ".join(text.split())
    lowered = normalized.lower()
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for requirement_type, terms, label in RULES:
        if requirement_type == "product" and "high strength" not in lowered:
            continue
        if any(term in lowered for term in terms) and requirement_type not in seen:
            results.append({
                "requirement_type": requirement_type,
                "requirement_text": label,
                "normalized_value": label,
            })
            seen.add(requirement_type)
    return results


def persist_requirements(client: Any, analysis_id: str, text: str) -> list[dict[str, Any]]:
    extracted = extract_requirements(text)
    if not extracted:
        return []
    existing = (
        client.table("extracted_requirements")
        .select("requirement_type, requirement_value")
        .eq("analysis_id", analysis_id)
        .execute()
        .data
        or []
    )
    existing_keys = {(row.get("requirement_type"), row.get("requirement_value")) for row in existing}
    rows = [
        {
            "analysis_id": analysis_id,
            "requirement_type": item["requirement_type"],
            "requirement_value": item["normalized_value"],
        }
        for item in extracted
        if (item["requirement_type"], item["normalized_value"]) not in existing_keys
    ]
    if rows:
        client.rpc(
            "insert_extracted_requirements",
            {
                "p_analysis_id": analysis_id,
                "p_requirements": [
                    {
                        "requirement_type": row["requirement_type"],
                        "requirement_value": row["requirement_value"],
                    }
                    for row in rows
                ],
            },
        ).execute()
    return extracted
