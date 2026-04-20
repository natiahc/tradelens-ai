from tradelens_ai.brokers.dhan import DhanBrokerAdapter
from tradelens_ai.domain.models import OrderSide, OrderType, ProductType


def test_dhan_build_place_order_payload_maps_fields():
    adapter = DhanBrokerAdapter(client_id="cid", access_token="token")

    payload = adapter._build_place_order_payload(
        request=type("Req", (), {
            "symbol": "1333",
            "exchange": "NSE_EQ",
            "side": OrderSide.BUY,
            "quantity": 5,
            "order_type": OrderType.LIMIT,
            "product_type": ProductType.CNC,
            "price": 100.5,
            "trigger_price": None,
            "client_order_id": "corr-1",
        })()
    )

    assert payload["securityId"] == "1333"
    assert payload["exchangeSegment"] == "NSE_EQ"
    assert payload["transactionType"] == "BUY"
    assert payload["orderType"] == "LIMIT"
    assert payload["productType"] == "CNC"
    assert payload["correlationId"] == "corr-1"


def test_dhan_map_order_defaults_safely():
    adapter = DhanBrokerAdapter(client_id="cid", access_token="token")
    order = adapter._map_order({})

    assert order.order_id == "unknown"
    assert order.quantity == 0
    assert order.filled_quantity == 0


def test_dhan_build_place_order_payload_keeps_stop_limit_shape():
    adapter = DhanBrokerAdapter(client_id="cid", access_token="token")

    payload = adapter._build_place_order_payload(
        request=type("Req", (), {
            "symbol": "500112",
            "exchange": "BSE_EQ",
            "side": OrderSide.SELL,
            "quantity": 2,
            "order_type": OrderType.STOP_LIMIT,
            "product_type": ProductType.MIS,
            "price": 812.0,
            "trigger_price": 810.0,
            "client_order_id": "corr-stop-1",
        })()
    )

    assert payload["securityId"] == "500112"
    assert payload["exchangeSegment"] == "BSE_EQ"
    assert payload["transactionType"] == "SELL"
    assert payload["quantity"] == 2
    assert payload["price"] == 812.0
    assert payload["triggerPrice"] == 810.0


def test_dhan_place_order_can_normalize_sparse_response():
    adapter = DhanBrokerAdapter(client_id="cid", access_token="token")

    class FakeClient:
        def place_order(self, payload):
            return {"orderId": "OID-1", "status": "pending"}

    adapter.client = FakeClient()
    request = type("Req", (), {
        "symbol": "1333",
        "exchange": "NSE_EQ",
        "side": OrderSide.BUY,
        "quantity": 5,
        "order_type": OrderType.LIMIT,
        "product_type": ProductType.CNC,
        "price": 100.5,
        "trigger_price": None,
        "client_order_id": "corr-2",
    })()

    order = adapter.place_order(request)
    assert order.order_id == "OID-1"
    assert order.symbol == "1333"
    assert order.quantity == 5
