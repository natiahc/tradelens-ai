import tempfile

from fastapi.testclient import TestClient

from tradelens_ai.api import app as fastapi_app
from tradelens_ai.api import app as api_module
from tradelens_ai.brokers.registry import build_default_registry
from tradelens_ai.persistence.sqlite_store import SQLiteStore
from tradelens_ai.services.audit_service import AuditService
from tradelens_ai.services.trading_service import TradingService


def build_test_client() -> TestClient:
    api_module.service = TradingService(build_default_registry())
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    api_module.audit_service = AuditService(SQLiteStore(temp_db.name))
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



def test_unknown_broker_returns_404():
    client = build_test_client()
    response = client.get("/orders/does-not-exist")

    assert response.status_code == 404
