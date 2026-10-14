from __future__ import annotations

import json
from typing import Any

from tradelens_ai.persistence.sqlite_store import AuditEvent, SQLiteStore


_SENSITIVE_KEYS = {
    "password", "passphrase", "secret", "api_secret", "api_key",
    "access_token", "refresh_token", "authorization",
    "client_secret", "master_key", "token", "credentials",
}


def _redact(value: Any) -> Any:
    """Sanitize structured audit payloads before writing to disk."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in _SENSITIVE_KEYS
            else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value[:100]]
    if isinstance(value, str):
        return value[:512]
    return value


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
            payload_json=json.dumps(_redact(payload), default=str),
        )

    def list_events(self, limit: int = 50) -> list[AuditEvent]:
        return self._store.list_audit_events(limit=limit)
