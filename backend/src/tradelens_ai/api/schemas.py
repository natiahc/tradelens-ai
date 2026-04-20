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
