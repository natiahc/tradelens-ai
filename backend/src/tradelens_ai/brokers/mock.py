from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.domain.models import (
    BrokerName,
    FundsSnapshot,
    Holding,
    Order,
    OrderRequest,
    OrderStatus,
    Position,
)


class MockBrokerAdapter(BrokerAdapter):
    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._positions: list[Position] = [
            Position(
                broker=BrokerName.MOCK,
                symbol="NIFTYETF",
                exchange="NSE",
                quantity=10,
                average_price=245.0,
                last_price=248.5,
            )
        ]
        self._holdings: list[Holding] = [
            Holding(
                broker=BrokerName.MOCK,
                symbol="INFY",
                exchange="NSE",
                quantity=5,
                average_price=1480.0,
                last_price=1512.5,
            )
        ]

    def broker_name(self) -> str:
        return BrokerName.MOCK.value

    def place_order(self, request: OrderRequest) -> Order:
        order_id = str(uuid4())
        order = Order(
            broker=BrokerName.MOCK,
            order_id=order_id,
            symbol=request.symbol,
            exchange=request.exchange,
            side=request.side,
            quantity=request.quantity,
            filled_quantity=0,
            order_type=request.order_type,
            product_type=request.product_type,
            status=OrderStatus.OPEN,
            price=request.price,
            average_price=None,
            created_at=datetime.utcnow(),
            raw_payload={"mock": True},
        )
        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Order:
        return self._orders[order_id]

    def list_orders(self) -> list[Order]:
        return list(self._orders.values())

    def cancel_order(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if order is None:
            return False
        self._orders[order_id] = replace(order, status=OrderStatus.CANCELLED)
        return True

    def list_positions(self) -> list[Position]:
        return list(self._positions)

    def list_holdings(self) -> list[Holding]:
        return list(self._holdings)

    def get_funds(self) -> FundsSnapshot:
        return FundsSnapshot(
            broker=BrokerName.MOCK,
            available_cash=100000.0,
            used_margin=12500.0,
            net_equity=112500.0,
        )
