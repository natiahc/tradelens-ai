import tempfile

from fastapi.testclient import TestClient

from tradelens_ai.api import app as fastapi_app
from tradelens_ai.api import app as api_module
from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.persistence.order_store import SQLiteOrderStore
from tradelens_ai.persistence.sqlite_store import SQLiteStore
from tradelens_ai.services.audit_service import AuditService
from tradelens_ai.services.broker_profile_service import BrokerProfileService
from tradelens_ai.services.order_history_service import OrderHistoryService
from tradelens_ai.services.risk_service import StrategyRiskService
from tradelens_ai.services.risk_settings_service import RiskSettingsService
from tradelens_ai.services.strategy_execution_service import StrategyExecutionService
from tradelens_ai.services.trading_service import TradingService


def build_test_client() -> TestClient:
    api_module.service = TradingService(build_default_registry())
    api_module.strategy_execution_service = StrategyExecutionService(api_module.service)
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    store = SQLiteStore(temp_db.name)
    api_module.audit_service = AuditService(store)
    api_module.order_history_service = OrderHistoryService(SQLiteOrderStore(temp_db.name))
    api_module.broker_profile_service = BrokerProfileService(temp_db.name)
    api_module.risk_settings_service = RiskSettingsService(temp_db.name)
    api_module.risk_service = StrategyRiskService(store, api_module.risk_settings_service)
    return TestClient(fastapi_app)



def test_health_endpoint_returns_ok():
    client = build_test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_brokers_endpoint_lists_mock_broker():
    client = build_test_client()
    response = client.get("/brokers")

    assert response.status_code == 200
    assert "mock" in response.json()["brokers"]



def test_get_broker_profile_returns_defaults():
    client = build_test_client()
    response = client.get("/broker-profile")

    assert response.status_code == 200
    body = response.json()
    assert body["broker_name"] == "mock"
    assert body["account_label"] == "Primary Paper Account"
    assert body["execution_mode"] == "paper"
    assert body["default_exchange"] == "NSE"
    assert body["default_product_type"] == "cnc"
    assert body["is_live_enabled"] is False



def test_update_broker_profile_persists_new_values():
    client = build_test_client()
    response = client.put(
        "/broker-profile",
        json={
            "broker_name": "dhan",
            "account_label": "Main Trading Account",
            "execution_mode": "live",
            "default_exchange": "NSE",
            "default_product_type": "mis",
            "is_live_enabled": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["broker_name"] == "dhan"
    assert body["account_label"] == "Main Trading Account"
    assert body["execution_mode"] == "live"
    assert body["default_exchange"] == "NSE"
    assert body["default_product_type"] == "mis"
    assert body["is_live_enabled"] is True

    follow_up = client.get("/broker-profile")
    assert follow_up.status_code == 200
    persisted = follow_up.json()
    assert persisted["broker_name"] == "dhan"
    assert persisted["execution_mode"] == "live"
    assert persisted["is_live_enabled"] is True



def test_get_risk_settings_returns_defaults():
    client = build_test_client()
    response = client.get("/risk/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["allowed_symbols"] == ["INFY", "TCS", "RELIANCE", "SBIN"]
    assert body["allowed_brokers"] == ["mock"]
    assert body["max_quantity"] == 10
    assert body["max_daily_strategy_executions"] == 20



def test_update_risk_settings_persists_new_values():
    client = build_test_client()
    response = client.put(
        "/risk/settings",
        json={
            "allowed_symbols": ["INFY", "TCS"],
            "allowed_brokers": ["mock"],
            "max_quantity": 3,
            "max_daily_strategy_executions": 7,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["allowed_symbols"] == ["INFY", "TCS"]
    assert body["allowed_brokers"] == ["mock"]
    assert body["max_quantity"] == 3
    assert body["max_daily_strategy_executions"] == 7

    follow_up = client.get("/risk/settings")
    assert follow_up.status_code == 200
    persisted = follow_up.json()
    assert persisted["max_quantity"] == 3
    assert persisted["max_daily_strategy_executions"] == 7



def test_place_order_and_list_orders_flow():
    client = build_test_client()

    create_response = client.post(
        "/orders",
        json={
            "broker": "mock",
            "symbol": "INFY",
            "exchange": "NSE",
            "side": "buy",
            "quantity": 3,
            "order_type": "market",
            "product_type": "cnc"
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["symbol"] == "INFY"

    list_response = client.get("/orders/mock")
    assert list_response.status_code == 200
    orders = list_response.json()
    assert len(orders) == 1
    assert orders[0]["order_id"] == created["order_id"]



def test_persisted_order_history_endpoint_contains_placed_order():
    client = build_test_client()

    create_response = client.post(
        "/orders",
        json={
            "broker": "mock",
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "side": "buy",
            "quantity": 4,
            "order_type": "market",
            "product_type": "cnc"
        },
    )
    created = create_response.json()

    history_response = client.get("/orders/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 1
    assert history[0]["order_id"] == created["order_id"]
    assert history[0]["symbol"] == "RELIANCE"



def test_cancel_order_endpoint_updates_order_state():
    client = build_test_client()

    create_response = client.post(
        "/orders",
        json={
            "broker": "mock",
            "symbol": "SBIN",
            "exchange": "NSE",
            "side": "sell",
            "quantity": 2,
            "order_type": "limit",
            "product_type": "mis",
            "price": 810.0
        },
    )
    order_id = create_response.json()["order_id"]

    cancel_response = client.delete(f"/orders/mock/{order_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    orders_response = client.get("/orders/mock")
    orders = orders_response.json()
    assert orders[0]["status"] == "cancelled"



def test_audit_events_endpoint_contains_order_activity():
    client = build_test_client()

    create_response = client.post(
        "/orders",
        json={
            "broker": "mock",
            "symbol": "TCS",
            "exchange": "NSE",
            "side": "buy",
            "quantity": 1,
            "order_type": "market",
            "product_type": "cnc"
        },
    )
    order_id = create_response.json()["order_id"]
    client.delete(f"/orders/mock/{order_id}")

    audit_response = client.get("/audit/events")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) >= 2
    event_types = {event["event_type"] for event in events}
    assert "order_placed" in event_types
    assert "order_cancelled" in event_types



def test_strategy_webhook_skipped_without_paper_trade_order():
    client = build_test_client()

    webhook_response = client.post(
        "/webhooks/strategy",
        json={
            "source": "tv-bridge",
            "signal_type": "entry_long",
            "broker": "mock",
            "payload": {"symbol": "INFY", "timeframe": "5m"}
        },
    )
    assert webhook_response.status_code == 200
    body = webhook_response.json()
    assert body["status"] == "accepted"
    assert body["executed"] is False
    assert body["blocked"] is False

    audit_response = client.get("/audit/events")
    events = audit_response.json()
    event_types = {event["event_type"] for event in events}
    assert "strategy_signal_received" in event_types
    assert "strategy_signal_skipped" in event_types



def test_strategy_webhook_blocks_disallowed_symbol():
    client = build_test_client()

    webhook_response = client.post(
        "/webhooks/strategy",
        json={
            "source": "tv-bridge",
            "signal_type": "entry_long",
            "broker": "mock",
            "payload": {
                "paper_trade_order": {
                    "symbol": "UNKNOWN",
                    "exchange": "NSE",
                    "side": "buy",
                    "quantity": 2,
                    "order_type": "market",
                    "product_type": "cnc"
                }
            }
        },
    )
    assert webhook_response.status_code == 200
    body = webhook_response.json()
    assert body["executed"] is False
    assert body["blocked"] is True
    assert "Symbol not allowed" in body["reason"]

    audit_response = client.get("/audit/events")
    events = audit_response.json()
    event_types = {event["event_type"] for event in events}
    assert "strategy_signal_blocked" in event_types



def test_strategy_webhook_blocks_excess_quantity():
    client = build_test_client()

    webhook_response = client.post(
        "/webhooks/strategy",
        json={
            "source": "tv-bridge",
            "signal_type": "entry_long",
            "broker": "mock",
            "payload": {
                "paper_trade_order": {
                    "symbol": "INFY",
                    "exchange": "NSE",
                    "side": "buy",
                    "quantity": 99,
                    "order_type": "market",
                    "product_type": "cnc"
                }
            }
        },
    )
    assert webhook_response.status_code == 200
    body = webhook_response.json()
    assert body["executed"] is False
    assert body["blocked"] is True
    assert "Quantity exceeds max limit" in body["reason"]



def test_strategy_webhook_executes_paper_trade_and_persists_order():
    client = build_test_client()

    webhook_response = client.post(
        "/webhooks/strategy",
        json={
            "source": "tv-bridge",
            "signal_type": "entry_long",
            "broker": "mock",
            "payload": {
                "paper_trade_order": {
                    "symbol": "INFY",
                    "exchange": "NSE",
                    "side": "buy",
                    "quantity": 2,
                    "order_type": "market",
                    "product_type": "cnc",
                    "client_order_id": "sig-1"
                }
            }
        },
    )
    assert webhook_response.status_code == 200
    body = webhook_response.json()
    assert body["status"] == "accepted"
    assert body["executed"] is True
    assert body["blocked"] is False
    assert body["order"]["symbol"] == "INFY"

    history_response = client.get("/orders/history")
    history = history_response.json()
    assert len(history) >= 1
    assert history[0]["symbol"] == "INFY"

    audit_response = client.get("/audit/events")
    events = audit_response.json()
    event_types = {event["event_type"] for event in events}
    assert "strategy_signal_received" in event_types
    assert "strategy_signal_executed" in event_types



def test_unknown_broker_returns_404():
    client = build_test_client()
    response = client.get("/orders/does-not-exist")

    assert response.status_code == 404
