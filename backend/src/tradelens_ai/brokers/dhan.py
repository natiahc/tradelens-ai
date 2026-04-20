from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.brokers.dhan_client import DhanApiClient
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


class DhanBrokerAdapter(BrokerAdapter):
    def __init__(self, client_id: str, access_token: str) -> None:
        self.client_id = client_id
        self.access_token = access_token
        self.client = DhanApiClient(client_id=client_id, access_token=access_token)

    def broker_name(self) -> str:
        return BrokerName.DHAN.value

    def _build_place_order_payload(self, request: OrderRequest) -> dict:
        return {
            "securityId": request.symbol,
            "exchangeSegment": request.exchange,
            "transactionType": request.side.value.upper(),
            "quantity": request.quantity,
            "orderType": request.order_type.value.upper(),
            "productType": request.product_type.value.upper(),
            "price": request.price,
            "triggerPrice": request.trigger_price,
            "correlationId": request.client_order_id,
        }

    def _map_order(self, payload: dict) -> Order:
        return Order(
            broker=BrokerName.DHAN,
            order_id=str(payload.get("orderId") or payload.get("orderNo") or "unknown"),
            symbol=str(payload.get("securityId") or payload.get("tradingSymbol") or ""),
            exchange=str(payload.get("exchangeSegment") or payload.get("exchange") or ""),
            side=request_side_from_payload(payload),
            quantity=int(payload.get("quantity") or payload.get("qty") or 0),
            filled_quantity=int(payload.get("filledQty") or payload.get("tradedQuantity") or 0),
            order_type=request_order_type_from_payload(payload),
            product_type=request_product_type_from_payload(payload),
            status=request_order_status_from_payload(payload),
            price=_to_optional_float(payload.get("price")),
            average_price=_to_optional_float(payload.get("avgTradedPrice") or payload.get("averageTradedPrice")),
            raw_payload=payload,
        )

    def place_order(self, request: OrderRequest) -> Order:
        payload = self._build_place_order_payload(request)
        response = self.client.place_order(payload)
        if isinstance(response, dict) and "data" in response and isinstance(response["data"], dict):
            return self._map_order(response["data"])
        if isinstance(response, dict):
            return self._map_order(response)
        raise ValueError("Unexpected Dhan place_order response format")

    def get_order(self, order_id: str) -> Order:
        orders = self.list_orders()
        for order in orders:
            if order.order_id == order_id:
                return order
        raise KeyError(f"Order not found: {order_id}")

    def list_orders(self) -> list[Order]:
        response = self.client.get_orders()
        items = response if isinstance(response, list) else response.get("data", [])
        return [self._map_order(item) for item in items]

    def cancel_order(self, order_id: str) -> bool:
        self.client.cancel_order(order_id)
        return True

    def list_positions(self) -> list[Position]:
        response = self.client.get_positions()
        items = response if isinstance(response, list) else response.get("data", [])
        return [
            Position(
                broker=BrokerName.DHAN,
                symbol=str(item.get("securityId") or item.get("tradingSymbol") or ""),
                exchange=str(item.get("exchangeSegment") or item.get("exchange") or ""),
                quantity=int(item.get("netQty") or item.get("quantity") or 0),
                average_price=float(item.get("costPrice") or item.get("averagePrice") or 0.0),
                last_price=float(item.get("ltp") or item.get("lastPrice") or 0.0),
            )
            for item in items
        ]

    def list_holdings(self) -> list[Holding]:
        response = self.client.get_holdings()
        items = response if isinstance(response, list) else response.get("data", [])
        return [
            Holding(
                broker=BrokerName.DHAN,
                symbol=str(item.get("securityId") or item.get("tradingSymbol") or ""),
                exchange=str(item.get("exchange") or item.get("exchangeSegment") or ""),
                quantity=int(item.get("totalQty") or item.get("quantity") or 0),
                average_price=float(item.get("avgCostPrice") or item.get("averagePrice") or 0.0),
                last_price=float(item.get("ltp") or item.get("lastPrice") or 0.0),
            )
            for item in items
        ]

    def get_funds(self) -> FundsSnapshot:
        response = self.client.get_funds()
        data = response.get("data", response)
        return FundsSnapshot(
            broker=BrokerName.DHAN,
            available_cash=float(data.get("availabelBalance") or data.get("availableBalance") or 0.0),
            used_margin=float(data.get("utilizedAmount") or data.get("usedMargin") or 0.0),
            net_equity=float(data.get("sodLimit") or data.get("netEquity") or 0.0),
        )


def _to_optional_float(value):
    if value is None or value == "":
        return None
    return float(value)



def request_side_from_payload(payload: dict) -> OrderSide:
    value = str(payload.get("transactionType", "BUY")).lower()
    return OrderSide.BUY if value == "buy" else OrderSide.SELL



def request_order_type_from_payload(payload: dict) -> OrderType:
    value = str(payload.get("orderType", "MARKET")).lower()
    mapping = {
        "market": OrderType.MARKET,
        "limit": OrderType.LIMIT,
        "stop": OrderType.STOP,
        "stop_limit": OrderType.STOP_LIMIT,
        "stoploss": OrderType.STOP,
        "sl": OrderType.STOP_LIMIT,
        "sl-m": OrderType.STOP,
    }
    return mapping.get(value, OrderType.MARKET)



def request_product_type_from_payload(payload: dict) -> ProductType:
    value = str(payload.get("productType", "CNC")).lower()
    mapping = {
        "cnc": ProductType.CNC,
        "mis": ProductType.MIS,
        "nrml": ProductType.NRML,
        "intraday": ProductType.MIS,
        "delivery": ProductType.CNC,
    }
    return mapping.get(value, ProductType.CNC)



def request_order_status_from_payload(payload: dict) -> OrderStatus:
    value = str(payload.get("orderStatus") or payload.get("status") or "created").strip().lower()
    mapping = {
        "created": OrderStatus.CREATED,
        "pending": OrderStatus.OPEN,
        "open": OrderStatus.OPEN,
        "transit": OrderStatus.OPEN,
        "trigger pending": OrderStatus.OPEN,
        "partially traded": OrderStatus.PARTIALLY_FILLED,
        "partially_filled": OrderStatus.PARTIALLY_FILLED,
        "filled": OrderStatus.FILLED,
        "traded": OrderStatus.FILLED,
        "cancelled": OrderStatus.CANCELLED,
        "canceled": OrderStatus.CANCELLED,
        "rejected": OrderStatus.REJECTED,
        "validation pending": OrderStatus.VALIDATED,
        "validated": OrderStatus.VALIDATED,
    }
    return mapping.get(value, OrderStatus.CREATED)
