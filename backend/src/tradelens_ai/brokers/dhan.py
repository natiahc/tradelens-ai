from __future__ import annotations

from tradelens_ai.brokers.base import BrokerAdapter
from tradelens_ai.brokers.dhan_client import DhanApiClient
from tradelens_ai.domain.models import (
    BrokerName,
    FundsSnapshot,
    Holding,
    Order,
    OrderRequest,
    OrderStatus,
    Position,
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
            order_id=str(payload.get("orderId", "unknown")),
            symbol=str(payload.get("securityId", "")),
            exchange=str(payload.get("exchangeSegment", "")),
            side=request_side_from_payload(payload),
            quantity=int(payload.get("quantity", 0)),
            filled_quantity=int(payload.get("filledQty", 0)),
            order_type=request_order_type_from_payload(payload),
            product_type=request_product_type_from_payload(payload),
            status=OrderStatus.CREATED,
            price=payload.get("price"),
            average_price=payload.get("avgTradedPrice"),
            raw_payload=payload,
        )

    def place_order(self, request: OrderRequest) -> Order:
        payload = self._build_place_order_payload(request)
        response = self.client.place_order(payload)
        return self._map_order(response)

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
                symbol=str(item.get("securityId", "")),
                exchange=str(item.get("exchangeSegment", "")),
                quantity=int(item.get("netQty", 0)),
                average_price=float(item.get("costPrice", 0.0)),
                last_price=float(item.get("ltp", 0.0)),
            )
            for item in items
        ]

    def list_holdings(self) -> list[Holding]:
        response = self.client.get_holdings()
        items = response if isinstance(response, list) else response.get("data", [])
        return [
            Holding(
                broker=BrokerName.DHAN,
                symbol=str(item.get("securityId", "")),
                exchange=str(item.get("exchange", "")),
                quantity=int(item.get("totalQty", 0)),
                average_price=float(item.get("avgCostPrice", 0.0)),
                last_price=float(item.get("ltp", 0.0)),
            )
            for item in items
        ]

    def get_funds(self) -> FundsSnapshot:
        response = self.client.get_funds()
        data = response.get("data", response)
        return FundsSnapshot(
            broker=BrokerName.DHAN,
            available_cash=float(data.get("availabelBalance", 0.0)),
            used_margin=float(data.get("utilizedAmount", 0.0)),
            net_equity=float(data.get("sodLimit", 0.0)),
        )


def request_side_from_payload(payload: dict):
    value = str(payload.get("transactionType", "BUY")).lower()
    from tradelens_ai.domain.models import OrderSide

    return OrderSide.BUY if value == "buy" else OrderSide.SELL



def request_order_type_from_payload(payload: dict):
    value = str(payload.get("orderType", "MARKET")).lower()
    from tradelens_ai.domain.models import OrderType

    mapping = {
        "market": OrderType.MARKET,
        "limit": OrderType.LIMIT,
        "stop": OrderType.STOP,
        "stop_limit": OrderType.STOP_LIMIT,
        "stoploss": OrderType.STOP,
        "sl": OrderType.STOP_LIMIT,
    }
    return mapping.get(value, OrderType.MARKET)



def request_product_type_from_payload(payload: dict):
    value = str(payload.get("productType", "CNC")).lower()
    from tradelens_ai.domain.models import ProductType

    mapping = {
        "cnc": ProductType.CNC,
        "mis": ProductType.MIS,
        "nrml": ProductType.NRML,
    }
    return mapping.get(value, ProductType.CNC)
