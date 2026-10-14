from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
    BrokerCredentialProfileResponse,
    BrokerCredentialProfileUpdateRequest,
    BrokerListResponse,
    BrokerProfileResponse,
    BrokerProfileUpdateRequest,
    HealthResponse,
    PersistedOrderResponse,
    PlaceOrderRequest,
    RiskSettingsResponse,
    RiskSettingsUpdateRequest,
    SmallCapitalPlanRequest,
    SmallCapitalBacktestRequest,
    StrategySummaryResponse,
    StrategyWebhookRequest,
)
from tradelens_ai.brokers.dhan import DhanBrokerAdapter
from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.config.settings import load_settings
from tradelens_ai.domain.models import OrderRequest, OrderSide, OrderType, ProductType
from tradelens_ai.persistence.order_store import SQLiteOrderStore
from tradelens_ai.persistence.sqlite_store import SQLiteStore
from tradelens_ai.services.audit_service import AuditService
from tradelens_ai.services.broker_credentials_service import BrokerCredentialsService
from tradelens_ai.services.broker_profile_service import BrokerProfile, BrokerProfileService
from tradelens_ai.services.order_history_service import OrderHistoryService
from tradelens_ai.services.risk_service import StrategyRiskService
from tradelens_ai.services.risk_settings_service import RiskSettings, RiskSettingsService
from tradelens_ai.services.small_capital_service import SmallCapitalLimits, plan_cash_equity_trade
from tradelens_ai.services.sma_backtest import DailyBar, backtest_sma
from tradelens_ai.services.strategy_execution_service import StrategyExecutionService
from tradelens_ai.services.strategy_summary_service import StrategySummaryService
from tradelens_ai.services.trading_service import TradingService



def require_admin(x_tradelens_admin_token: str | None = Header(default=None)) -> None:
    """Protect private operational and trading endpoints; no public fallback."""
    expected = os.getenv("TRADELENS_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin API locked. Configure TRADELENS_ADMIN_TOKEN in Render.",
        )
    if not x_tradelens_admin_token or not secrets.compare_digest(expected, x_tradelens_admin_token):
        raise HTTPException(status_code=401, detail="Valid admin access token required")


settings = load_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)


def _load_cors_origins() -> list[str]:
    raw = os.getenv("TRADELENS_CORS_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _load_cors_origin_regex() -> str | None:
    raw = os.getenv("TRADELENS_CORS_ORIGIN_REGEX", "").strip()
    if raw:
        return raw
    return r"https://.*\.vercel\.app|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?"


class DisabledBrokerCredentialsService:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def get_profile(self):
        raise RuntimeError(self.reason)

    def update_profile(self, **kwargs):
        raise RuntimeError(self.reason)

    def reveal_secrets(self):
        raise RuntimeError(self.reason)


cors_origins = _load_cors_origins()
cors_origin_regex = None if cors_origins == ["*"] else _load_cors_origin_regex()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)
registry = build_default_registry(settings)
service = TradingService(registry)
strategy_execution_service = StrategyExecutionService(service)
db_path = os.getenv("TRADELENS_DATABASE_PATH", "tradelens_ai.db")
audit_store = SQLiteStore(db_path)
audit_service = AuditService(audit_store)
order_store = SQLiteOrderStore(db_path)
order_history_service = OrderHistoryService(order_store)
broker_profile_service = BrokerProfileService(db_path)
try:
    broker_credentials_service = BrokerCredentialsService(db_path)
except Exception as exc:
    broker_credentials_service = DisabledBrokerCredentialsService(
        f"Broker credentials service is unavailable: {exc}"
    )
risk_settings_service = RiskSettingsService(db_path)
risk_service = StrategyRiskService(audit_store, risk_settings_service)
strategy_summary_service = StrategySummaryService(audit_store)


def _sync_dynamic_brokers_from_credentials() -> None:
    try:
        secrets = broker_credentials_service.reveal_secrets()
    except RuntimeError:
        return

    broker_name = str(secrets.get("broker_name") or "").strip().lower()
    client_id = str(secrets.get("client_id") or "").strip()
    access_token = str(secrets.get("access_token") or "").strip()

    if broker_name == "dhan" and client_id and access_token:
        registry.register(DhanBrokerAdapter(client_id=client_id, access_token=access_token))


_sync_dynamic_brokers_from_credentials()



def _diagnose_application() -> dict:
    """Safe, curated capability report without secrets or broker requests."""
    findings: list[dict] = []
    try:
        with sqlite3.connect(db_path, timeout=3) as conn:
            conn.execute("SELECT 1").fetchone()
        findings.append({
            "id": "sqlite", "status": "pass",
            "message": "Persistent database connection succeeded.",
        })
    except (sqlite3.Error, OSError):
        findings.append({
            "id": "sqlite", "status": "fail",
            "message": "Database unavailable. Check Render disk mount /var/data and permissions.",
        })
    configured = bool(os.getenv("TRADELENS_ADMIN_TOKEN", "").strip())
    findings.append({
        "id": "admin_access",
        "status": "pass" if configured else "blocked",
        "message": (
            "Admin access is configured. Enter your token in the dashboard."
            if configured else
            "Set TRADELENS_ADMIN_TOKEN on the existing Render service; "
            "private operational APIs stay locked until configured."
        ),
    })
    findings.append({
        "id": "live_orders", "status": "pass",
        "message": "Live broker automation is not supported by the paper-only audit workflow.",
    })
    findings.append({
        "id": "historical_data", "status": "manual",
        "message": "Upload OHLC CSV in Small Capital Lab. No automatic NSE live-data feed is configured.",
    })
    return {
        "application": "TradeLens AI",
        "mode": "paper_research",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "capabilities": [
            {"name": "Health", "method": "GET", "path": "/health", "admin": False},
            {"name": "Diagnostics", "method": "GET", "path": "/diagnostics/status", "admin": False},
            {"name": "Paper position plan", "method": "POST", "path": "/strategy/small-capital/plan", "admin": False},
            {"name": "OHLC SMA backtest", "method": "POST", "path": "/strategy/small-capital/backtest", "admin": False},
            {"name": "Run and persist audit", "method": "POST", "path": "/diagnostics/run", "admin": True},
            {"name": "Read saved diagnostics", "method": "GET", "path": "/diagnostics/logs", "admin": True},
            {"name": "Broker management", "method": "GET/PUT", "path": "/broker-profile", "admin": True},
            {"name": "Broker secrets (disabled until admin access)", "method": "GET/PUT", "path": "/broker-credentials", "admin": True},
            {"name": "Mock order", "method": "POST", "path": "/orders", "admin": True},
        ],
        "limitations": [
            "No automatic live NSE market-data or broker execution",
            "Historical simulation cannot demonstrate assured profits",
            "Production access control requires TRADELENS_ADMIN_TOKEN on Render",
            "Live API trading is disabled by default",
        ],
    }


@app.get("/diagnostics/status", tags=["diagnostics"])
def diagnostics_status():
    return _diagnose_application()


@app.post("/diagnostics/run", tags=["diagnostics"], dependencies=[Depends(require_admin)])
def diagnostics_run():
    report = _diagnose_application()
    audit_service.log_event(
        event_type="diagnostic_run",
        broker_name=None,
        entity_id=None,
        payload={
            "checks": [{"id": item["id"], "status": item["status"]} for item in report["findings"]],
            "timestamp_utc": report["timestamp_utc"],
        },
    )
    return report


@app.get("/diagnostics/logs", tags=["diagnostics"], dependencies=[Depends(require_admin)])
def diagnostics_logs(limit: int = 100):
    """Bounded saved diagnostic events; no request bodies or secrets."""
    rows = audit_service.list_events(limit=max(1, min(limit, 200)))
    return [
        {
            "id": event.event_id,
            "event": event.event_type,
            "timestamp_utc": event.created_at,
            "summary": event.payload_json[:1024] if event.event_type == "diagnostic_run" else "{}",
        }
        for event in rows if event.event_type == "diagnostic_run"
    ]


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/brokers", response_model=BrokerListResponse, tags=["brokers"], dependencies=[Depends(require_admin)])
def list_brokers() -> BrokerListResponse:
    _sync_dynamic_brokers_from_credentials()
    return BrokerListResponse(brokers=service.list_brokers())


@app.get("/broker-profile", response_model=BrokerProfileResponse, tags=["brokers"], dependencies=[Depends(require_admin)])
def get_broker_profile() -> BrokerProfileResponse:
    profile = broker_profile_service.get_profile()
    return BrokerProfileResponse(
        broker_name=profile.broker_name,
        account_label=profile.account_label,
        execution_mode=profile.execution_mode,
        default_exchange=profile.default_exchange,
        default_product_type=profile.default_product_type,
        is_live_enabled=profile.is_live_enabled,
    )


@app.put("/broker-profile", response_model=BrokerProfileResponse, tags=["brokers"], dependencies=[Depends(require_admin)])
def update_broker_profile(payload: BrokerProfileUpdateRequest) -> BrokerProfileResponse:
    updated = broker_profile_service.update_profile(
        BrokerProfile(
            broker_name=payload.broker_name.strip(),
            account_label=payload.account_label.strip(),
            execution_mode=payload.execution_mode.strip(),
            default_exchange=payload.default_exchange.strip().upper(),
            default_product_type=payload.default_product_type.strip().lower(),
            is_live_enabled=payload.is_live_enabled,
        )
    )
    audit_service.log_event(
        event_type="broker_profile_updated",
        broker_name=updated.broker_name,
        entity_id=None,
        payload={
            "broker_name": updated.broker_name,
            "account_label": updated.account_label,
            "execution_mode": updated.execution_mode,
            "default_exchange": updated.default_exchange,
            "default_product_type": updated.default_product_type,
            "is_live_enabled": updated.is_live_enabled,
        },
    )
    return BrokerProfileResponse(
        broker_name=updated.broker_name,
        account_label=updated.account_label,
        execution_mode=updated.execution_mode,
        default_exchange=updated.default_exchange,
        default_product_type=updated.default_product_type,
        is_live_enabled=updated.is_live_enabled,
    )


@app.get("/broker-credentials", response_model=BrokerCredentialProfileResponse, tags=["brokers"], dependencies=[Depends(require_admin)])
def get_broker_credentials() -> BrokerCredentialProfileResponse:
    try:
        profile = broker_credentials_service.get_profile()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return BrokerCredentialProfileResponse(
        broker_name=profile.broker_name,
        client_id_hint=profile.client_id_hint,
        api_key_hint=profile.api_key_hint,
        has_access_token=profile.has_access_token,
        has_api_secret=profile.has_api_secret,
        updated_at=profile.updated_at,
    )


@app.put("/broker-credentials", response_model=BrokerCredentialProfileResponse, tags=["brokers"], dependencies=[Depends(require_admin)])
def update_broker_credentials(payload: BrokerCredentialProfileUpdateRequest) -> BrokerCredentialProfileResponse:
    try:
        updated = broker_credentials_service.update_profile(
            broker_name=payload.broker_name.strip(),
            client_id=payload.client_id,
            api_key=payload.api_key,
            access_token=payload.access_token,
            api_secret=payload.api_secret,
        )
        _sync_dynamic_brokers_from_credentials()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    audit_service.log_event(
        event_type="broker_credentials_updated",
        broker_name=updated.broker_name,
        entity_id=None,
        payload={
            "broker_name": updated.broker_name,
            "client_id_hint": updated.client_id_hint,
            "api_key_hint": updated.api_key_hint,
            "has_access_token": updated.has_access_token,
            "has_api_secret": updated.has_api_secret,
            "updated_at": updated.updated_at,
        },
    )
    return BrokerCredentialProfileResponse(
        broker_name=updated.broker_name,
        client_id_hint=updated.client_id_hint,
        api_key_hint=updated.api_key_hint,
        has_access_token=updated.has_access_token,
        has_api_secret=updated.has_api_secret,
        updated_at=updated.updated_at,
    )


@app.get("/risk/settings", response_model=RiskSettingsResponse, tags=["risk"], dependencies=[Depends(require_admin)])
def get_risk_settings() -> RiskSettingsResponse:
    current = risk_settings_service.get_settings()
    return RiskSettingsResponse(
        allowed_symbols=current.allowed_symbols,
        allowed_brokers=current.allowed_brokers,
        max_quantity=current.max_quantity,
        max_daily_strategy_executions=current.max_daily_strategy_executions,
    )


@app.put("/risk/settings", response_model=RiskSettingsResponse, tags=["risk"], dependencies=[Depends(require_admin)])
def update_risk_settings(payload: RiskSettingsUpdateRequest) -> RiskSettingsResponse:
    updated = risk_settings_service.update_settings(
        RiskSettings(
            allowed_symbols=[symbol.strip().upper() for symbol in payload.allowed_symbols if symbol.strip()],
            allowed_brokers=[broker.strip() for broker in payload.allowed_brokers if broker.strip()],
            max_quantity=payload.max_quantity,
            max_daily_strategy_executions=payload.max_daily_strategy_executions,
        )
    )
    audit_service.log_event(
        event_type="risk_settings_updated",
        broker_name=None,
        entity_id=None,
        payload={
            "allowed_symbols": updated.allowed_symbols,
            "allowed_brokers": updated.allowed_brokers,
            "max_quantity": updated.max_quantity,
            "max_daily_strategy_executions": updated.max_daily_strategy_executions,
        },
    )
    return RiskSettingsResponse(
        allowed_symbols=updated.allowed_symbols,
        allowed_brokers=updated.allowed_brokers,
        max_quantity=updated.max_quantity,
        max_daily_strategy_executions=updated.max_daily_strategy_executions,
    )


@app.get("/strategy/summary", response_model=StrategySummaryResponse, tags=["strategy"], dependencies=[Depends(require_admin)])
def get_strategy_summary() -> StrategySummaryResponse:
    summary = strategy_summary_service.get_summary()
    return StrategySummaryResponse(
        signals_received=summary.signals_received,
        executed=summary.executed,
        blocked=summary.blocked,
        skipped=summary.skipped,
    )


@app.post("/strategy/small-capital/plan", tags=["strategy"])
def small_capital_plan(payload: SmallCapitalPlanRequest):
    """Size a hypothetical NSE cash-equity trade. NEVER places an order."""
    try:
        plan = plan_cash_equity_trade(
            symbol=payload.symbol,
            entry_price=payload.entry_price,
            stop_price=payload.stop_price,
            available_cash_rupees=payload.available_cash_rupees,
            daily_realized_pnl_rupees=payload.daily_realized_pnl_rupees,
            existing_symbol_exposure_rupees=payload.existing_symbol_exposure_rupees,
            limits=SmallCapitalLimits(capital_rupees=payload.capital_rupees),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return plan.to_dict()


@app.post("/strategy/small-capital/backtest", tags=["strategy"])
def small_capital_backtest(payload: SmallCapitalBacktestRequest):
    """Research only. Consumes caller-supplied history; no broker or DB writes."""
    if payload.fast_days >= payload.slow_days:
        raise HTTPException(status_code=422, detail="fast_days must be less than slow_days")
    if len(payload.bars) <= payload.slow_days:
        raise HTTPException(
            status_code=422,
            detail="Provide more sessions than the slow moving-average window",
        )
    try:
        bars = [
            DailyBar(date=date.fromisoformat(item.date), open=item.open,
                     high=item.high, low=item.low, close=item.close)
            for item in payload.bars
        ]
        return backtest_sma(
            bars, symbol=payload.symbol,
            fast_days=payload.fast_days, slow_days=payload.slow_days,
            stop_pct=payload.stop_pct,
            limits=SmallCapitalLimits(capital_rupees=payload.capital_rupees),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/orders", tags=["orders"], dependencies=[Depends(require_admin)])
def place_order(payload: PlaceOrderRequest):
    # The API has no production authentication yet. Never send real orders by
    # default, even when broker credentials have been configured.
    if payload.broker.strip().lower() != "mock" and os.getenv(
        "TRADELENS_ALLOW_LIVE_ORDERS", "false"
    ).strip().lower() != "true":
        raise HTTPException(
            status_code=403,
            detail="Live broker orders are disabled; use mock paper trading",
        )
    _sync_dynamic_brokers_from_credentials()
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


@app.get("/orders/history", response_model=list[PersistedOrderResponse], tags=["orders"], dependencies=[Depends(require_admin)])
def list_persisted_orders(limit: int = 100):
    return [to_persisted_order_response(order) for order in order_history_service.list_orders(limit=limit)]


@app.get("/orders/{broker_name}", tags=["orders"], dependencies=[Depends(require_admin)])
def list_orders(broker_name: str):
    _sync_dynamic_brokers_from_credentials()
    try:
        return [to_order_response(order) for order in service.list_orders(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/orders/{broker_name}/{order_id}", tags=["orders"], dependencies=[Depends(require_admin)])
def cancel_order(broker_name: str, order_id: str):
    _sync_dynamic_brokers_from_credentials()
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


@app.post("/webhooks/strategy", tags=["strategy"], dependencies=[Depends(require_admin)])
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

    risk_decision = risk_service.evaluate(broker_name=payload.broker, payload=payload.payload)
    if not risk_decision.allowed:
        audit_service.log_event(
            event_type="strategy_signal_blocked",
            broker_name=payload.broker,
            entity_id=None,
            payload={
                "signal_type": payload.signal_type,
                "source": payload.source,
                "reason": risk_decision.reason,
            },
        )
        return {
            "status": "accepted",
            "event_id": event_id,
            "executed": False,
            "blocked": True,
            "reason": risk_decision.reason,
        }

    _sync_dynamic_brokers_from_credentials()
    execution = strategy_execution_service.maybe_execute_signal(
        broker_name=payload.broker,
        signal_type=payload.signal_type,
        payload=payload.payload,
    )

    response = {"status": "accepted", "event_id": event_id, "executed": execution.executed, "blocked": False}

    if execution.order is not None:
        order_history_service.record_order(execution.order)
        audit_service.log_event(
            event_type="strategy_signal_executed",
            broker_name=execution.broker,
            entity_id=execution.order.order_id,
            payload={
                "signal_type": payload.signal_type,
                "source": payload.source,
                "order_id": execution.order.order_id,
                "reason": execution.reason,
            },
        )
        response["order"] = to_order_response(execution.order).model_dump()
    else:
        audit_service.log_event(
            event_type="strategy_signal_skipped",
            broker_name=execution.broker,
            entity_id=None,
            payload={
                "signal_type": payload.signal_type,
                "source": payload.source,
                "reason": execution.reason,
            },
        )
        response["reason"] = execution.reason

    return response


@app.get("/positions/{broker_name}", tags=["portfolio"], dependencies=[Depends(require_admin)])
def list_positions(broker_name: str):
    _sync_dynamic_brokers_from_credentials()
    try:
        return [to_position_response(position) for position in service.list_positions(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/holdings/{broker_name}", tags=["portfolio"], dependencies=[Depends(require_admin)])
def list_holdings(broker_name: str):
    _sync_dynamic_brokers_from_credentials()
    try:
        return [to_holding_response(holding) for holding in service.list_holdings(broker_name)]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/funds/{broker_name}", tags=["portfolio"], dependencies=[Depends(require_admin)])
def get_funds(broker_name: str):
    _sync_dynamic_brokers_from_credentials()
    try:
        return to_funds_response(service.get_funds(broker_name))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/audit/events", response_model=list[AuditEventResponse], tags=["audit"], dependencies=[Depends(require_admin)])
def list_audit_events(limit: int = 50):
    return [to_audit_event_response(event) for event in audit_service.list_events(limit=limit)]
