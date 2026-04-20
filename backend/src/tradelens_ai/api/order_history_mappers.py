from __future__ import annotations

from tradelens_ai.api.schemas import PersistedOrderResponse
from tradelens_ai.persistence.order_store import PersistedOrder


def to_persisted_order_response(order: PersistedOrder) -> PersistedOrderResponse:
    return PersistedOrderResponse(
        record_id=order.record_id,
        broker_name=order.broker_name,
        order_id=order.order_id,
        symbol=order.symbol,
        exchange=order.exchange,
        side=order.side,
        quantity=order.quantity,
        filled_quantity=order.filled_quantity,
        order_type=order.order_type,
        product_type=order.product_type,
        status=order.status,
        price=order.price,
        average_price=order.average_price,
        created_at=order.created_at,
    )
