from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.brokers.dhan import DhanBrokerAdapter
from tradelens_ai.brokers.mock import MockBrokerAdapter
from tradelens_ai.brokers.zerodha import ZerodhaBrokerAdapter
from tradelens_ai.config.settings import AppSettings


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



def build_default_registry(settings: AppSettings | None = None) -> BrokerRegistry:
    registry = BrokerRegistry()

    if settings is None or settings.enable_mock_broker:
        registry.register(MockBrokerAdapter())

    if (
        settings is not None
        and settings.broker_api is not None
        and settings.broker_api.dhan_client_id
        and settings.broker_api.dhan_access_token
    ):
        registry.register(
            DhanBrokerAdapter(
                client_id=settings.broker_api.dhan_client_id,
                access_token=settings.broker_api.dhan_access_token,
            )
        )

    if (
        settings is not None
        and settings.broker_api is not None
        and settings.broker_api.zerodha_api_key
        and settings.broker_api.zerodha_access_token
    ):
        registry.register(
            ZerodhaBrokerAdapter(
                api_key=settings.broker_api.zerodha_api_key,
                access_token=settings.broker_api.zerodha_access_token,
            )
        )

    return registry
