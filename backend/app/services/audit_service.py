from typing import Any


def record_event(client: Any, user_id: str, action: str, resource_type: str, resource_id: str | None = None,
                 metadata: dict[str, Any] | None = None) -> None:
    client.rpc(
        "insert_audit_log",
        {
            "p_action": action,
            "p_entity_type": resource_type,
            "p_entity_id": resource_id,
            "p_metadata": metadata or {},
        },
    ).execute()
