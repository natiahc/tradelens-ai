from __future__ import annotations

from pprint import pprint

from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType


def main() -> None:
    registry = build_default_registry()
    broker = registry.get("mock")

    order = broker.place_order(
        OrderRequest(
            symbol="INFY",
            exchange="NSE",
            side=OrderSide.BUY,
            quantity=2,
            order_type=OrderType.MARKET,
            product_type=ProductType.CNC,
        )
    )

    print("Registered brokers:")
    pprint(registry.list_brokers())

    print("\nPlaced order:")
    pprint(order)

    print("\nFunds snapshot:")
    pprint(broker.get_funds())

    print("\nOpen orders:")
    pprint(broker.list_orders())

    print("\nPositions:")
    pprint(broker.list_positions())

    print("\nHoldings:")
    pprint(broker.list_holdings())


if __name__ == "__main__":
    main()
