from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.brokers.registry import BrokerRegistry
from tradelens_ai.domain.models import FundsSnapshot, Holding, Order, OrderRequest, Position


class TradingService:
    def __init__(self, registry: BrokerRegistry) -> None:
        self._registry = registry

    def list_brokers(self) -> list[str]:
        return self._registry.list_brokers()

    def get_broker(self, broker_name: str) -> BrokerAdapter:
        return self._registry.get(broker_name)

    def place_order(self, broker_name: str, request: OrderRequest) -> Order:
        return self.get_broker(broker_name).place_order(request)

    def list_orders(self, broker_name: str) -> list[Order]:
        return self.get_broker(broker_name).list_orders()

    def list_positions(self, broker_name: str) -> list[Position]:
        return self.get_broker(broker_name).list_positions()

    def list_holdings(self, broker_name: str) -> list[Holding]:
        return self.get_broker(broker_name).list_holdings()

    def get_funds(self, broker_name: str) -> FundsSnapshot:
        return self.get_broker(broker_name).get_funds()

    def cancel_order(self, broker_name: str, order_id: str) -> bool:
        return self.get_broker(broker_name).cancel_order(order_id)
