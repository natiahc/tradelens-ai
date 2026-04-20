from __future__ import annotations

from dataclasses import dataclass
import sqlite3


@dataclass(slots=True)
class BrokerProfile:
    broker_name: str
    account_label: str
    execution_mode: str
    default_exchange: str
    default_product_type: str
    is_live_enabled: bool


class BrokerProfileService:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        default = BrokerProfile(
            broker_name="mock",
            account_label="Primary Paper Account",
            execution_mode="paper",
            default_exchange="NSE",
            default_product_type="cnc",
            is_live_enabled=False,
        )
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS broker_profiles (
                    profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
                    broker_name TEXT NOT NULL,
                    account_label TEXT NOT NULL,
                    execution_mode TEXT NOT NULL,
                    default_exchange TEXT NOT NULL,
                    default_product_type TEXT NOT NULL,
                    is_live_enabled INTEGER NOT NULL
                )
                """
            )
            existing = connection.execute(
                "SELECT profile_id FROM broker_profiles WHERE profile_id = 1"
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO broker_profiles (
                        profile_id, broker_name, account_label, execution_mode,
                        default_exchange, default_product_type, is_live_enabled
                    ) VALUES (1, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        default.broker_name,
                        default.account_label,
                        default.execution_mode,
                        default.default_exchange,
                        default.default_product_type,
                        1 if default.is_live_enabled else 0,
                    ),
                )
            connection.commit()

    def get_profile(self) -> BrokerProfile:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT broker_name, account_label, execution_mode,
                       default_exchange, default_product_type, is_live_enabled
                FROM broker_profiles
                WHERE profile_id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Broker profile not initialized")
        return BrokerProfile(
            broker_name=str(row["broker_name"]),
            account_label=str(row["account_label"]),
            execution_mode=str(row["execution_mode"]),
            default_exchange=str(row["default_exchange"]),
            default_product_type=str(row["default_product_type"]),
            is_live_enabled=bool(row["is_live_enabled"]),
        )

    def update_profile(self, profile: BrokerProfile) -> BrokerProfile:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE broker_profiles
                SET broker_name = ?,
                    account_label = ?,
                    execution_mode = ?,
                    default_exchange = ?,
                    default_product_type = ?,
                    is_live_enabled = ?
                WHERE profile_id = 1
                """,
                (
                    profile.broker_name,
                    profile.account_label,
                    profile.execution_mode,
                    profile.default_exchange,
                    profile.default_product_type,
                    1 if profile.is_live_enabled else 0,
                ),
            )
            connection.commit()
        return self.get_profile()
