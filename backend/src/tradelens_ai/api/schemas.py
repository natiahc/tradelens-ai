from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class PlaceOrderRequest(BaseModel):
    broker: str = Field(..., description="Registered broker name")
    symbol: str
    exchange: str
    side: str
    quantity: int = Field(..., gt=0)
    order_type: str
    product_type: str
    price: Optional[float] = None
    trigger_price: Optional[float] = None


class StrategyWebhookRequest(BaseModel):
    source: str = Field(..., description="Signal source name")
    signal_type: str
    broker: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class BrokerListResponse(BaseModel):
    brokers: list[str]


class BrokerProfileResponse(BaseModel):
    broker_name: str
    account_label: str
    execution_mode: str
    default_exchange: str
    default_product_type: str
    is_live_enabled: bool


class BrokerProfileUpdateRequest(BaseModel):
    broker_name: str
    account_label: str
    execution_mode: str
    default_exchange: str
    default_product_type: str
    is_live_enabled: bool


class BrokerCredentialProfileResponse(BaseModel):
    broker_name: str
    client_id_hint: str
    api_key_hint: str
    has_access_token: bool
    has_api_secret: bool
    updated_at: str


class BrokerCredentialProfileUpdateRequest(BaseModel):
    broker_name: str
    client_id: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    api_secret: Optional[str] = None


class StrategySummaryResponse(BaseModel):
    signals_received: int
    executed: int
    blocked: int
    skipped: int


class RiskSettingsResponse(BaseModel):
    allowed_symbols: list[str]
    allowed_brokers: list[str]
    max_quantity: int
    max_daily_strategy_executions: int


class RiskSettingsUpdateRequest(BaseModel):
    allowed_symbols: list[str]
    allowed_brokers: list[str]
    max_quantity: int = Field(..., gt=0)
    max_daily_strategy_executions: int = Field(..., gt=0)


class OrderResponse(BaseModel):
    broker: str
    order_id: str
    symbol: str
    exchange: str
    side: str
    quantity: int
    filled_quantity: int
    order_type: str
    product_type: str
    status: str
    price: Optional[float] = None
    average_price: Optional[float] = None
    created_at: str


class PersistedOrderResponse(BaseModel):
    record_id: int
    broker_name: str
    order_id: str
    symbol: str
    exchange: str
    side: str
    quantity: int
    filled_quantity: int
    order_type: str
    product_type: str
    status: str
    price: Optional[float] = None
    average_price: Optional[float] = None
    created_at: str


class FundsResponse(BaseModel):
    broker: str
    available_cash: float
    used_margin: float
    net_equity: float


class PositionResponse(BaseModel):
    broker: str
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float
    unrealized_pnl: float


class HoldingResponse(BaseModel):
    broker: str
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float


class AuditEventResponse(BaseModel):
    event_id: int
    event_type: str
    broker_name: Optional[str] = None
    entity_id: Optional[str] = None
    payload_json: str
    created_at: str


class SmallCapitalPlanRequest(BaseModel):
    """Read-only trade sizing; this endpoint cannot place orders."""

    symbol: str
    entry_price: float = Field(..., gt=0)
    stop_price: float = Field(..., gt=0)
    available_cash_rupees: float = Field(..., ge=0)
    daily_realized_pnl_rupees: float = 0.0
    existing_symbol_exposure_rupees: float = Field(0.0, ge=0)
    capital_rupees: float = Field(25_000.0, gt=0)


class DailyBarInput(BaseModel):
    """Unadjusted OHLC for one historical trading session."""

    date: str = Field(..., description="Trading session YYYY-MM-DD")
    open: float = Field(..., gt=0, allow_inf_nan=False)
    high: float = Field(..., gt=0, allow_inf_nan=False)
    low: float = Field(..., gt=0, allow_inf_nan=False)
    close: float = Field(..., gt=0, allow_inf_nan=False)


class SmallCapitalBacktestRequest(BaseModel):
    """Ephemeral research only. Prices are supplied by the caller."""

    symbol: str = Field("INFY", min_length=1, max_length=25)
    capital_rupees: float = Field(25_000.0, ge=1_000, le=100_000_000, allow_inf_nan=False)
    fast_days: int = Field(20, ge=2, le=250)
    slow_days: int = Field(50, ge=3, le=500)
    stop_pct: float = Field(0.02, gt=0, lt=1, allow_inf_nan=False)
    bars: list[DailyBarInput] = Field(..., min_length=4, max_length=2000)
