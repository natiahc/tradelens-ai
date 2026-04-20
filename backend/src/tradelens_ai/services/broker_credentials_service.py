from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from datetime import datetime, timezone


@dataclass(slots=True)
class BrokerCredentialProfile:
    broker_name: str
    client_id_hint: str
    api_key_hint: str
    has_access_token: bool
    has_api_secret: bool
    updated_at: str


class BrokerCredentialsService:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS broker_credentials (
                    credentials_id INTEGER PRIMARY KEY CHECK (credentials_id = 1),
                    broker_name TEXT NOT NULL,
                    client_id_hint TEXT NOT NULL,
                    api_key_hint TEXT NOT NULL,
                    has_access_token INTEGER NOT NULL,
                    has_api_secret INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            existing = connection.execute(
                "SELECT credentials_id FROM broker_credentials WHERE credentials_id = 1"
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO broker_credentials (
                        credentials_id, broker_name, client_id_hint, api_key_hint,
                        has_access_token, has_api_secret, updated_at
                    ) VALUES (1, ?, ?, ?, ?, ?, ?)
                    """,
                    ("mock", "", "", 0, 0, self._now_iso()),
                )
            connection.commit()

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_profile(self) -> BrokerCredentialProfile:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT broker_name, client_id_hint, api_key_hint,
                       has_access_token, has_api_secret, updated_at
                FROM broker_credentials
                WHERE credentials_id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Broker credential profile not initialized")
        return BrokerCredentialProfile(
            broker_name=str(row["broker_name"]),
            client_id_hint=str(row["client_id_hint"]),
            api_key_hint=str(row["api_key_hint"]),
            has_access_token=bool(row["has_access_token"]),
            has_api_secret=bool(row["has_api_secret"]),
            updated_at=str(row["updated_at"]),
        )

    def update_profile(
        self,
        *,
        broker_name: str,
        client_id: str | None,
        api_key: str | None,
        access_token: str | None,
        api_secret: str | None,
    ) -> BrokerCredentialProfile:
        client_id_hint = _mask_secret(client_id)
        api_key_hint = _mask_secret(api_key)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE broker_credentials
                SET broker_name = ?,
                    client_id_hint = ?,
                    api_key_hint = ?,
                    has_access_token = ?,
                    has_api_secret = ?,
                    updated_at = ?
                WHERE credentials_id = 1
                """,
                (
                    broker_name,
                    client_id_hint,
                    api_key_hint,
                    1 if bool(access_token) else 0,
                    1 if bool(api_secret) else 0,
                    self._now_iso(),
                ),
            )
            connection.commit()
        return self.get_profile()


def _mask_secret(value: str | None) -> str:
    if not value:
        return ""
    trimmed = value.strip()
    if len(trimmed) <= 4:
        return "*" * len(trimmed)
    return f"{trimmed[:2]}{'*' * (len(trimmed) - 4)}{trimmed[-2:]}"
