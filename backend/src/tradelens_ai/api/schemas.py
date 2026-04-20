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
