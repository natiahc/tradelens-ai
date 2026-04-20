from tradelens_ai.brokers.zerodha import ZerodhaBrokerAdapter
from tradelens_ai.domain.models import OrderSide, OrderStatus, OrderType, ProductType


def test_zerodha_build_place_order_payload_maps_fields():
    adapter = ZerodhaBrokerAdapter(api_key="key", access_token="token")

    payload = adapter._build_place_order_payload(
        request=type("Req", (), {
            "symbol": "INFY",
            "exchange": "NSE",
            "side": OrderSide.BUY,
            "quantity": 10,
            "order_type": OrderType.LIMIT,
            "product_type": ProductType.CNC,
            "price": 1510.5,
            "trigger_price": None,
            "client_order_id": "tag-1",
        })()
    )

    assert payload["tradingsymbol"] == "INFY"
    assert payload["transaction_type"] == "BUY"
    assert payload["order_type"] == "LIMIT"
    assert payload["product"] == "CNC"
    assert payload["tag"] == "tag-1"


def test_zerodha_map_order_status_complete_to_filled():
    adapter = ZerodhaBrokerAdapter(api_key="key", access_token="token")
    order = adapter._map_order(
        {
            "order_id": "OID123",
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "transaction_type": "BUY",
            "quantity": 10,
            "filled_quantity": 10,
            "order_type": "LIMIT",
            "product": "CNC",
            "status": "COMPLETE",
            "price": 1500,
            "average_price": 1499.5,
        }
    )

    assert order.order_id == "OID123"
    assert order.status == OrderStatus.FILLED
    assert order.quantity == 10
    assert order.filled_quantity == 10
