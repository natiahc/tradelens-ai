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
from tradelens_ai.config.settings import load_settings
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType
from tradelens_ai.services.trading_service import TradingService

settings = load_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
registry = build_default_registry(settings)
service = TradingService(registry)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/brokers", response_model=BrokerListResponse, tags=["brokers"])
def list_brokers() -> BrokerListResponse:
    return BrokerListResponse(brokers=service.list_brokers())


@app.post("/orders", tags=["orders"])
def place_order(payload: PlaceOrderRequest):
    try:
        order = service.place_order(
            payload.broker,
            OrderRequest(
                symbol=payload.symbol,
                exchange=payload.exchange,
                side=OrderSide(payload.side.lower()),
                quantity=payload.quantity,
                order_type=OrderType(payload.order_type.lower()),
                product_type=ProductType(payload.product_type.lower()),
                price=payload.price,
                trigger_price=payload.trigger_price,
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_order_response(order)


@app.get("/orders/{broker_name}", tags=["orders"])
def list_orders(broker_name: str):
    try:
        return [to_order_response(order) for order in service.list_orders(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/orders/{broker_name}/{order_id}", tags=["orders"])
def cancel_order(broker_name: str, order_id: str):
    try:
        is_cancelled = service.cancel_order(broker_name, order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not is_cancelled:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    return {"status": "cancelled", "order_id": order_id, "broker": broker_name}


@app.get("/positions/{broker_name}", tags=["portfolio"])
def list_positions(broker_name: str):
    try:
        return [to_position_response(position) for position in service.list_positions(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/holdings/{broker_name}", tags=["portfolio"])
def list_holdings(broker_name: str):
    try:
        return [to_holding_response(holding) for holding in service.list_holdings(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/funds/{broker_name}", tags=["portfolio"])
def get_funds(broker_name: str):
    try:
        return to_funds_response(service.get_funds(broker_name))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
