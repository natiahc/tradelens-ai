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
