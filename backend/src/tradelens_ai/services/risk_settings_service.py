from __future__ import annotations

import json
from dataclasses import dataclass
import sqlite3


@dataclass(slots=True)
class RiskSettings:
    allowed_symbols: list[str]
    allowed_brokers: list[str]
    max_quantity: int
    max_daily_strategy_executions: int


class RiskSettingsService:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        default = RiskSettings(
            allowed_symbols=["INFY", "TCS", "RELIANCE", "SBIN"],
            allowed_brokers=["mock"],
            max_quantity=10,
            max_daily_strategy_executions=20,
        )
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_settings (
                    settings_id INTEGER PRIMARY KEY CHECK (settings_id = 1),
                    allowed_symbols_json TEXT NOT NULL,
                    allowed_brokers_json TEXT NOT NULL,
                    max_quantity INTEGER NOT NULL,
                    max_daily_strategy_executions INTEGER NOT NULL
                )
                """
            )
            existing = connection.execute(
                "SELECT settings_id FROM risk_settings WHERE settings_id = 1"
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO risk_settings (
                        settings_id, allowed_symbols_json, allowed_brokers_json,
                        max_quantity, max_daily_strategy_executions
                    ) VALUES (1, ?, ?, ?, ?)
                    """,
                    (
                        json.dumps(default.allowed_symbols),
                        json.dumps(default.allowed_brokers),
                        default.max_quantity,
                        default.max_daily_strategy_executions,
                    ),
                )
            connection.commit()

    def get_settings(self) -> RiskSettings:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT allowed_symbols_json, allowed_brokers_json,
                       max_quantity, max_daily_strategy_executions
                FROM risk_settings
                WHERE settings_id = 1
                """
            ).fetchone()
        if row is None:
            raise RuntimeError("Risk settings not initialized")
        return RiskSettings(
            allowed_symbols=list(json.loads(row["allowed_symbols_json"])),
            allowed_brokers=list(json.loads(row["allowed_brokers_json"])),
            max_quantity=int(row["max_quantity"]),
            max_daily_strategy_executions=int(row["max_daily_strategy_executions"]),
        )

    def update_settings(self, settings: RiskSettings) -> RiskSettings:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE risk_settings
                SET allowed_symbols_json = ?,
                    allowed_brokers_json = ?,
                    max_quantity = ?,
                    max_daily_strategy_executions = ?
                WHERE settings_id = 1
                """,
                (
                    json.dumps(settings.allowed_symbols),
                    json.dumps(settings.allowed_brokers),
                    settings.max_quantity,
                    settings.max_daily_strategy_executions,
                ),
            )
            connection.commit()
        return self.get_settings()
