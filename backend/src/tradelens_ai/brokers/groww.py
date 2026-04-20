from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.domain.models import FundsSnapshot, Holding, Order, OrderRequest, Position


class GrowwBrokerAdapter(BrokerAdapter):
    def __init__(self, client_id: str, access_token: str) -> None:
        self.client_id = client_id
        self.access_token = access_token

    def broker_name(self) -> str:
        return "groww"

    def place_order(self, request: OrderRequest) -> Order:
        raise NotImplementedError("Groww adapter not implemented yet")

    def get_order(self, order_id: str) -> Order:
        raise NotImplementedError("Groww adapter not implemented yet")

    def list_orders(self) -> list[Order]:
        raise NotImplementedError("Groww adapter not implemented yet")

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError("Groww adapter not implemented yet")

    def list_positions(self) -> list[Position]:
        raise NotImplementedError("Groww adapter not implemented yet")

    def list_holdings(self) -> list[Holding]:
        raise NotImplementedError("Groww adapter not implemented yet")

    def get_funds(self) -> FundsSnapshot:
        raise NotImplementedError("Groww adapter not implemented yet")
