from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType
from tradelens_ai.services.trading_service import TradingService


def test_mock_broker_can_place_and_list_order():
    registry = build_default_registry()
    service = TradingService(registry)

    order = service.place_order(
        "mock",
        OrderRequest(
            symbol="INFY",
            exchange="NSE",
            side=OrderSide.BUY,
            quantity=1,
            order_type=OrderType.MARKET,
            product_type=ProductType.CNC,
        ),
    )

    orders = service.list_orders("mock")

    assert order.symbol == "INFY"
    assert len(orders) == 1
    assert orders[0].order_id == order.order_id


def test_mock_broker_cancel_order():
    registry = build_default_registry()
    service = TradingService(registry)

    order = service.place_order(
        "mock",
        OrderRequest(
            symbol="SBIN",
            exchange="NSE",
            side=OrderSide.SELL,
            quantity=2,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            price=810.0,
        ),
    )

    assert service.cancel_order("mock", order.order_id) is True
