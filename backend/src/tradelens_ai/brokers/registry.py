from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.brokers.mock import MockBrokerAdapter


class BrokerRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, BrokerAdapter] = {}

    def register(self, adapter: BrokerAdapter) -> None:
        self._adapters[adapter.broker_name()] = adapter

    def get(self, broker_name: str) -> BrokerAdapter:
        if broker_name not in self._adapters:
            raise KeyError(f"Broker adapter not registered: {broker_name}")
        return self._adapters[broker_name]

    def list_brokers(self) -> list[str]:
        return sorted(self._adapters.keys())


def build_default_registry() -> BrokerRegistry:
    registry = BrokerRegistry()
    registry.register(MockBrokerAdapter())
    return registry
