import json

from fastapi.testclient import TestClient

from tradelens_ai.api import app
from tradelens_ai.api import app as fastapi_app
from tradelens_ai.services.audit_service import AuditService
from tradelens_ai.persistence.sqlite_store import SQLiteStore


def admin_headers():
    return {"X-TradeLens-Admin-Token": "test-tradelens-token"}


def test_public_diagnostics_status_has_no_secrets():
    response = TestClient(app).get("/diagnostics/status")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "paper_research"
    assert any(c["path"] == "/strategy/small-capital/backtest" for c in body["capabilities"])
    assert "test-tradelens-token" not in response.text


def test_private_endpoints_require_authentication():
    client = TestClient(app)
    for path in ["/broker-credentials", "/risk/settings", "/audit/events", "/diagnostics/logs"]:
        response = client.get(path)
        assert response.status_code == 401, path
    assert client.post("/orders", json={
        "broker": "mock", "symbol": "INFY", "exchange": "NSE",
        "side": "buy", "quantity": 1, "order_type": "market", "product_type": "cnc",
    }).status_code == 401


def test_admin_api_fail_closed_when_missing_server_token(monkeypatch):
    monkeypatch.delenv("TRADELENS_ADMIN_TOKEN", raising=False)
    assert TestClient(app).get("/audit/events").status_code == 503


def test_incorrect_admin_token_rejected():
    assert TestClient(app).get("/diagnostics/logs", headers={
        "X-TradeLens-Admin-Token": "wrong"
    }).status_code == 401


def test_saved_diagnostics_can_be_retrieved_with_admin_token():
    with TestClient(app, headers=admin_headers()) as client:
        saved = client.post("/diagnostics/run")
        assert saved.status_code == 200
        rows = client.get("/diagnostics/logs").json()
        assert any(event["event"] == "diagnostic_run" for event in rows)
        assert "test-tradelens-token" not in json.dumps(rows)


def test_paper_trade_planner_stays_public():
    client = TestClient(app)
    result = client.post("/strategy/small-capital/plan", json={
        "symbol": "INFY", "entry_price": 100, "stop_price": 98,
        "available_cash_rupees": 25000
    })
    assert result.status_code == 200
    assert result.json()["paper_only"] is True


def test_audit_redacts_nested_secret_values(tmp_path):
    service = AuditService(SQLiteStore(str(tmp_path / "audit.db")))
    service.log_event(
        event_type="test", broker_name="mock", entity_id=None,
        payload={"access_token": "never-store-me", "nested": {
            "api_key": "never-store-this-either", "normal": "fine"
        }},
    )
    stored = service.list_events()[0].payload_json
    assert "never-store-me" not in stored
    assert "never-store-this-either" not in stored
    assert stored.count("[REDACTED]") == 2
