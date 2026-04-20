from __future__ import annotations

from tradelens_ai.api.schemas import AuditEventResponse
from tradelens_ai.persistence.sqlite_store import AuditEvent


def to_audit_event_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        event_id=event.event_id,
        event_type=event.event_type,
        broker_name=event.broker_name,
        entity_id=event.entity_id,
        payload_json=event.payload_json,
        created_at=event.created_at,
    )
