from __future__ import annotations

from fastapi import FastAPI, HTTPException

from tradelens_ai.api.mappers import (
    to_funds_response,
    to_holding_response,
    to_order_response,
    to_position_response,
)
from tradelens_ai.api.schemas import BrokerListResponse, HealthResponse, PlaceOrderRequest
from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType

app = FastAPI(title="TradeLens AI", version="0.1.0")
registry = build_default_registry()


def _get_broker_or_404(broker_name: str):
    try:
        return registry.get(broker_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/brokers", response_model=BrokerListResponse)
def list_brokers() -> BrokerListResponse:
    return BrokerListResponse(brokers=registry.list_brokers())


@app.post("/orders")
def place_order(payload: PlaceOrderRequest):
    broker = _get_broker_or_404(payload.broker)
    try:
        order = broker.place_order(
            OrderRequest(
                symbol=payload.symbol,
                exchange=payload.exchange,
                side=OrderSide(payload.side.lower()),
                quantity=payload.quantity,
                order_type=OrderType(payload.order_type.lower()),
                product_type=ProductType(payload.product_type.lower()),
                price=payload.price,
                trigger_price=payload.trigger_price,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_order_response(order)


@app.get("/orders/{broker_name}")
def list_orders(broker_name: str):
    broker = _get_broker_or_404(broker_name)
    return [to_order_response(order) for order in broker.list_orders()]


@app.get("/positions/{broker_name}")
def list_positions(broker_name: str):
    broker = _get_broker_or_404(broker_name)
    return [to_position_response(position) for position in broker.list_positions()]


@app.get("/holdings/{broker_name}")
def list_holdings(broker_name: str):
    broker = _get_broker_or_404(broker_name)
    return [to_holding_response(holding) for holding in broker.list_holdings()]


@app.get("/funds/{broker_name}")
def get_funds(broker_name: str):
    broker = _get_broker_or_404(broker_name)
    return to_funds_response(broker.get_funds())
