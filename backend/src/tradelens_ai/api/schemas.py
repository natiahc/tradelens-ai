from __future__ import annotations

from typing import Optional

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


class BrokerListResponse(BaseModel):
    brokers: list[str]


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
