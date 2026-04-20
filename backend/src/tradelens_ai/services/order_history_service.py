from __future__ import annotations

from tradelens_ai.domain.models import Order
from tradelens_ai.persistence.order_store import PersistedOrder, SQLiteOrderStore


class OrderHistoryService:
    def __init__(self, store: SQLiteOrderStore) -> None:
        self._store = store

    def record_order(self, order: Order) -> int:
        return self._store.insert_order(
            broker_name=order.broker.value,
            order_id=order.order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side.value,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            order_type=order.order_type.value,
            product_type=order.product_type.value,
            status=order.status.value,
            price=order.price,
            average_price=order.average_price,
        )

    def list_orders(self, limit: int = 100) -> list[PersistedOrder]:
        return self._store.list_orders(limit=limit)
