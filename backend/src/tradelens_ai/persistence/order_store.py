from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional


@dataclass(slots=True)
class PersistedOrder:
    record_id: int
    broker_name: str
    order_id: str
    symbol: str
    exchange: str
    side: str
    quantity: int
    filled_quantity: int
    order_type: str
    product_type: str
    status: str
    price: Optional[float]
    average_price: Optional[float]
    created_at: str


class SQLiteOrderStore:
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
                CREATE TABLE IF NOT EXISTS persisted_orders (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    broker_name TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    filled_quantity INTEGER NOT NULL,
                    order_type TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price REAL,
                    average_price REAL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def insert_order(
        self,
        *,
        broker_name: str,
        order_id: str,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        filled_quantity: int,
        order_type: str,
        product_type: str,
        status: str,
        price: Optional[float],
        average_price: Optional[float],
    ) -> int:
        created_at = datetime.utcnow().isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO persisted_orders (
                    broker_name, order_id, symbol, exchange, side, quantity, filled_quantity,
                    order_type, product_type, status, price, average_price, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    broker_name,
                    order_id,
                    symbol,
                    exchange,
                    side,
                    quantity,
                    filled_quantity,
                    order_type,
                    product_type,
                    status,
                    price,
                    average_price,
                    created_at,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_orders(self, limit: int = 100) -> list[PersistedOrder]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT record_id, broker_name, order_id, symbol, exchange, side, quantity,
                       filled_quantity, order_type, product_type, status, price, average_price, created_at
                FROM persisted_orders
                ORDER BY record_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            PersistedOrder(
                record_id=int(row["record_id"]),
                broker_name=str(row["broker_name"]),
                order_id=str(row["order_id"]),
                symbol=str(row["symbol"]),
                exchange=str(row["exchange"]),
                side=str(row["side"]),
                quantity=int(row["quantity"]),
                filled_quantity=int(row["filled_quantity"]),
                order_type=str(row["order_type"]),
                product_type=str(row["product_type"]),
                status=str(row["status"]),
                price=row["price"],
                average_price=row["average_price"],
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]
