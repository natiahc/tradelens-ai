from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Any


@dataclass(slots=True)
class AuditEvent:
    event_id: int
    event_type: str
    broker_name: str | None
    entity_id: str | None
    payload_json: str
    created_at: str


class SQLiteStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    broker_name TEXT,
                    entity_id TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def insert_audit_event(
        self,
        *,
        event_type: str,
        broker_name: str | None,
        entity_id: str | None,
        payload_json: str,
    ) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO audit_events (event_type, broker_name, entity_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, broker_name, entity_id, payload_json, created_at),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_audit_events(self, limit: int = 50) -> list[AuditEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, event_type, broker_name, entity_id, payload_json, created_at
                FROM audit_events
                ORDER BY event_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            AuditEvent(
                event_id=int(row["event_id"]),
                event_type=str(row["event_type"]),
                broker_name=row["broker_name"],
                entity_id=row["entity_id"],
                payload_json=str(row["payload_json"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]
