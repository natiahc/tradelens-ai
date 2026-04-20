from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from tradelens_ai.api.audit_mappers import to_audit_event_response
from tradelens_ai.api.mappers import (
    to_funds_response,
    to_holding_response,
    to_order_response,
    to_position_response,
)
from tradelens_ai.api.order_history_mappers import to_persisted_order_response
from tradelens_ai.api.schemas import (
    AuditEventResponse,
    BrokerListResponse,
    HealthResponse,
    PersistedOrderResponse,
    PlaceOrderRequest,
    StrategyWebhookRequest,
)
from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.config.settings import load_settings
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType
from tradelens_ai.persistence.order_store import SQLiteOrderStore
from tradelens_ai.persistence.sqlite_store import SQLiteStore
from tradelens_ai.services.audit_service import AuditService
from tradelens_ai.services.order_history_service import OrderHistoryService
from tradelens_ai.services.trading_service import TradingService

settings = load_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
registry = build_default_registry(settings)
service = TradingService(registry)
db_path = os.getenv("TRADELENS_DATABASE_PATH", "tradelens_ai.db")
audit_store = SQLiteStore(db_path)
audit_service = AuditService(audit_store)
order_store = SQLiteOrderStore(db_path)
order_history_service = OrderHistoryService(order_store)


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

    order_history_service.record_order(order)
    audit_service.log_event(
        event_type="order_placed",
        broker_name=payload.broker,
        entity_id=order.order_id,
        payload={
            "symbol": payload.symbol,
            "exchange": payload.exchange,
            "side": payload.side,
            "quantity": payload.quantity,
            "order_type": payload.order_type,
            "product_type": payload.product_type,
        },
    )
    return to_order_response(order)


@app.get("/orders/{broker_name}", tags=["orders"])
def list_orders(broker_name: str):
    try:
        return [to_order_response(order) for order in service.list_orders(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/orders/history", response_model=list[PersistedOrderResponse], tags=["orders"])
def list_persisted_orders(limit: int = 100):
    return [to_persisted_order_response(order) for order in order_history_service.list_orders(limit=limit)]


@app.delete("/orders/{broker_name}/{order_id}", tags=["orders"])
def cancel_order(broker_name: str, order_id: str):
    try:
        is_cancelled = service.cancel_order(broker_name, order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not is_cancelled:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")

    audit_service.log_event(
        event_type="order_cancelled",
        broker_name=broker_name,
        entity_id=order_id,
        payload={"order_id": order_id, "broker": broker_name},
    )
    return {"status": "cancelled", "order_id": order_id, "broker": broker_name}


@app.post("/webhooks/strategy", tags=["strategy"])
def strategy_webhook(payload: StrategyWebhookRequest):
    event_id = audit_service.log_event(
        event_type="strategy_signal_received",
        broker_name=payload.broker,
        entity_id=None,
        payload={
            "source": payload.source,
            "signal_type": payload.signal_type,
            "broker": payload.broker,
            "payload": payload.payload,
        },
    )
    return {"status": "accepted", "event_id": event_id}


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


@app.get("/audit/events", response_model=list[AuditEventResponse], tags=["audit"])
def list_audit_events(limit: int = 50):
    return [to_audit_event_response(event) for event in audit_service.list_events(limit=limit)]
