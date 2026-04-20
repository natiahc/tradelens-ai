from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tradelens_ai.domain.models import Order, OrderRequest, OrderSide, OrderType, ProductType
from tradelens_ai.services.trading_service import TradingService


@dataclass(slots=True)
class StrategyExecutionResult:
    accepted: bool
    executed: bool
    broker: str | None = None
    order: Order | None = None
    reason: str | None = None


class StrategyExecutionService:
    def __init__(self, trading_service: TradingService) -> None:
        self._trading_service = trading_service

    def maybe_execute_signal(
        self,
        *,
        broker_name: str | None,
        signal_type: str,
        payload: dict[str, Any],
    ) -> StrategyExecutionResult:
        if not broker_name:
            return StrategyExecutionResult(
                accepted=True,
                executed=False,
                reason="No broker provided for execution",
            )

        paper_order = payload.get("paper_trade_order")
        if not isinstance(paper_order, dict):
            return StrategyExecutionResult(
                accepted=True,
                executed=False,
                broker=broker_name,
                reason="No paper_trade_order payload provided",
            )

        try:
            request = self._build_order_request(paper_order)
            order = self._trading_service.place_order(broker_name, request)
        except (KeyError, ValueError) as exc:
            return StrategyExecutionResult(
                accepted=True,
                executed=False,
                broker=broker_name,
                reason=str(exc),
            )

        return StrategyExecutionResult(
            accepted=True,
            executed=True,
            broker=broker_name,
            order=order,
            reason=f"Signal {signal_type} executed as paper trade",
        )

    def _build_order_request(self, payload: dict[str, Any]) -> OrderRequest:
        return OrderRequest(
            symbol=str(payload["symbol"]),
            exchange=str(payload["exchange"]),
            side=OrderSide(str(payload["side"]).lower()),
            quantity=int(payload["quantity"]),
            order_type=OrderType(str(payload["order_type"]).lower()),
            product_type=ProductType(str(payload["product_type"]).lower()),
            price=float(payload["price"]) if payload.get("price") is not None else None,
            trigger_price=float(payload["trigger_price"]) if payload.get("trigger_price") is not None else None,
            client_order_id=str(payload["client_order_id"]) if payload.get("client_order_id") is not None else None,
        )
