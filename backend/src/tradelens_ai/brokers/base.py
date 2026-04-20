from __future__ import annotations

from abc import ABC, abstractmethod

from tradelens_ai.domain.models import FundsSnapshot, Holding, Order, OrderRequest, Position


class BrokerAdapter(ABC):
    @abstractmethod
    def broker_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def place_order(self, request: OrderRequest) -> Order:
        raise NotImplementedError

    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        raise NotImplementedError

    @abstractmethod
    def list_orders(self) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_positions(self) -> list[Position]:
        raise NotImplementedError

    @abstractmethod
    def list_holdings(self) -> list[Holding]:
        raise NotImplementedError

    @abstractmethod
    def get_funds(self) -> FundsSnapshot:
        raise NotImplementedError
