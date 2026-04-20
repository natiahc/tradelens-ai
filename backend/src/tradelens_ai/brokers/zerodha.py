from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.domain.models import FundsSnapshot, Holding, Order, OrderRequest, Position


class ZerodhaBrokerAdapter(BrokerAdapter):
    def __init__(self, api_key: str, access_token: str) -> None:
        self.api_key = api_key
        self.access_token = access_token

    def broker_name(self) -> str:
        return "zerodha"

    def place_order(self, request: OrderRequest) -> Order:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def get_order(self, order_id: str) -> Order:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def list_orders(self) -> list[Order]:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def list_positions(self) -> list[Position]:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def list_holdings(self) -> list[Holding]:
        raise NotImplementedError("Zerodha adapter not implemented yet")

    def get_funds(self) -> FundsSnapshot:
        raise NotImplementedError("Zerodha adapter not implemented yet")
