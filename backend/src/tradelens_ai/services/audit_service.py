from __future__ import annotations

import json
from typing import Any

from tradelens_ai.persistence.sqlite_store import AuditEvent, SQLiteStore


class AuditService:
    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    def log_event(
        self,
        *,
        event_type: str,
        broker_name: str | None,
        entity_id: str | None,
        payload: dict[str, Any],
    ) -> int:
        return self._store.insert_audit_event(
            event_type=event_type,
            broker_name=broker_name,
            entity_id=entity_id,
            payload_json=json.dumps(payload, default=str),
        )

    def list_events(self, limit: int = 50) -> list[AuditEvent]:
        return self._store.list_audit_events(limit=limit)
