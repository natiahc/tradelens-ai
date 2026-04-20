from __future__ import annotations

from tradelens_ai.api.schemas import FundsResponse, HoldingResponse, OrderResponse, PositionResponse
from tradelens_ai.domain.models import FundsSnapshot, Holding, Order, Position


def to_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        broker=order.broker.value,
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
        created_at=order.created_at.isoformat(),
    )


def to_funds_response(funds: FundsSnapshot) -> FundsResponse:
    return FundsResponse(
        broker=funds.broker.value,
        available_cash=funds.available_cash,
        used_margin=funds.used_margin,
        net_equity=funds.net_equity,
    )


def to_position_response(position: Position) -> PositionResponse:
    return PositionResponse(
        broker=position.broker.value,
        symbol=position.symbol,
        exchange=position.exchange,
        quantity=position.quantity,
        average_price=position.average_price,
        last_price=position.last_price,
        unrealized_pnl=position.unrealized_pnl,
    )


def to_holding_response(holding: Holding) -> HoldingResponse:
    return HoldingResponse(
        broker=holding.broker.value,
        symbol=holding.symbol,
        exchange=holding.exchange,
        quantity=holding.quantity,
        average_price=holding.average_price,
        last_price=holding.last_price,
    )
