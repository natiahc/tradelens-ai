from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class BrokerApiSettings:
    dhan_client_id: str | None = None
    dhan_access_token: str | None = None
    zerodha_api_key: str | None = None
    zerodha_access_token: str | None = None
    groww_client_id: str | None = None
    groww_access_token: str | None = None


@dataclass(slots=True)
class AppSettings:
    app_name: str = "TradeLens AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    enable_mock_broker: bool = True
    broker_api: BrokerApiSettings | None = None



def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}



def load_settings() -> AppSettings:
    broker_api = BrokerApiSettings(
        dhan_client_id=os.getenv("DHAN_CLIENT_ID"),
        dhan_access_token=os.getenv("DHAN_ACCESS_TOKEN"),
        zerodha_api_key=os.getenv("ZERODHA_API_KEY"),
        zerodha_access_token=os.getenv("ZERODHA_ACCESS_TOKEN"),
        groww_client_id=os.getenv("GROWW_CLIENT_ID"),
        groww_access_token=os.getenv("GROWW_ACCESS_TOKEN"),
    )

    return AppSettings(
        app_name=os.getenv("TRADELENS_APP_NAME", "TradeLens AI"),
        app_version=os.getenv("TRADELENS_APP_VERSION", "0.1.0"),
        environment=os.getenv("TRADELENS_ENV", "development"),
        enable_mock_broker=_to_bool(os.getenv("TRADELENS_ENABLE_MOCK_BROKER"), True),
        broker_api=broker_api,
    )
