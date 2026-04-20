from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.domain.models import (
    BrokerName,
    FundsSnapshot,
    Holding,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    ProductType,
)


class ZerodhaBrokerAdapter(BrokerAdapter):
    def __init__(self, api_key: str, access_token: str) -> None:
        self.api_key = api_key
        self.access_token = access_token

    def broker_name(self) -> str:
        return BrokerName.ZERODHA.value

    def _build_place_order_payload(self, request: OrderRequest) -> dict:
        return {
            "tradingsymbol": request.symbol,
            "exchange": request.exchange,
            "transaction_type": request.side.value.upper(),
            "quantity": request.quantity,
            "order_type": request.order_type.value.upper(),
            "product": request.product_type.value.upper(),
            "price": request.price,
            "trigger_price": request.trigger_price,
            "tag": request.client_order_id,
            "variety": "regular",
        }

    def _map_order(self, payload: dict) -> Order:
        return Order(
            broker=BrokerName.ZERODHA,
            order_id=str(payload.get("order_id") or payload.get("orderId") or "unknown"),
            symbol=str(payload.get("tradingsymbol") or payload.get("symbol") or ""),
            exchange=str(payload.get("exchange") or ""),
            side=_side_from_payload(payload),
            quantity=int(payload.get("quantity") or 0),
            filled_quantity=int(payload.get("filled_quantity") or payload.get("filledQuantity") or 0),
            order_type=_order_type_from_payload(payload),
            product_type=_product_type_from_payload(payload),
            status=_order_status_from_payload(payload),
            price=_to_optional_float(payload.get("price")),
            average_price=_to_optional_float(payload.get("average_price") or payload.get("averagePrice")),
            raw_payload=payload,
        )

    def place_order(self, request: OrderRequest) -> Order:
        payload = self._build_place_order_payload(request)
        return self._map_order(payload)

    def get_order(self, order_id: str) -> Order:
        raise NotImplementedError("Zerodha live fetch not implemented yet")

    def list_orders(self) -> list[Order]:
        raise NotImplementedError("Zerodha live list not implemented yet")

    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError("Zerodha live cancel not implemented yet")

    def list_positions(self) -> list[Position]:
        raise NotImplementedError("Zerodha live positions not implemented yet")

    def list_holdings(self) -> list[Holding]:
        raise NotImplementedError("Zerodha live holdings not implemented yet")

    def get_funds(self) -> FundsSnapshot:
        raise NotImplementedError("Zerodha live funds not implemented yet")


def _to_optional_float(value):
    if value is None or value == "":
        return None
    return float(value)


def _side_from_payload(payload: dict) -> OrderSide:
    value = str(payload.get("transaction_type") or payload.get("side") or "BUY").lower()
    return OrderSide.BUY if value == "buy" else OrderSide.SELL


def _order_type_from_payload(payload: dict) -> OrderType:
    value = str(payload.get("order_type") or "MARKET").lower()
    mapping = {
        "market": OrderType.MARKET,
        "limit": OrderType.LIMIT,
        "sl": OrderType.STOP_LIMIT,
        "sl-m": OrderType.STOP,
        "stop": OrderType.STOP,
        "stop_limit": OrderType.STOP_LIMIT,
    }
    return mapping.get(value, OrderType.MARKET)


def _product_type_from_payload(payload: dict) -> ProductType:
    value = str(payload.get("product") or "CNC").lower()
    mapping = {
        "cnc": ProductType.CNC,
        "mis": ProductType.MIS,
        "nrml": ProductType.NRML,
    }
    return mapping.get(value, ProductType.CNC)


def _order_status_from_payload(payload: dict) -> OrderStatus:
    value = str(payload.get("status") or "created").strip().lower()
    mapping = {
        "created": OrderStatus.CREATED,
        "open": OrderStatus.OPEN,
        "trigger pending": OrderStatus.OPEN,
        "complete": OrderStatus.FILLED,
        "filled": OrderStatus.FILLED,
        "cancelled": OrderStatus.CANCELLED,
        "rejected": OrderStatus.REJECTED,
        "validated": OrderStatus.VALIDATED,
        "put order req received": OrderStatus.VALIDATED,
    }
    return mapping.get(value, OrderStatus.CREATED)
