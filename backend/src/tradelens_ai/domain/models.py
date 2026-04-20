from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BrokerName(str, Enum):
    MOCK = "mock"
    DHAN = "dhan"
    ZERODHA = "zerodha"
    GROWW = "groww"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class ProductType(str, Enum):
    CNC = "cnc"
    MIS = "mis"
    NRML = "nrml"


class OrderStatus(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(slots=True)
class BrokerCredentials:
    broker: BrokerName
    client_id: str
    access_token: str
    refresh_token: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class OrderRequest:
    symbol: str
    exchange: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    product_type: ProductType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    client_order_id: Optional[str] = None


@dataclass(slots=True)
class Order:
    broker: BrokerName
    order_id: str
    symbol: str
    exchange: str
    side: OrderSide
    quantity: int
    filled_quantity: int
    order_type: OrderType
    product_type: ProductType
    status: OrderStatus
    price: Optional[float] = None
    average_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    raw_payload: dict = field(default_factory=dict)


@dataclass(slots=True)
class Position:
    broker: BrokerName
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float

    @property
    def unrealized_pnl(self) -> float:
        return (self.last_price - self.average_price) * self.quantity


@dataclass(slots=True)
class Holding:
    broker: BrokerName
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    last_price: float


@dataclass(slots=True)
class FundsSnapshot:
    broker: BrokerName
    available_cash: float
    used_margin: float
    net_equity: float
