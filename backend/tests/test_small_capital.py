import math

import pytest
from fastapi.testclient import TestClient

from tradelens_ai.api import app
from tradelens_ai.services.small_capital_service import (
    SmallCapitalLimits,
    plan_cash_equity_trade,
)


def test_small_account_limits_position_and_risk():
    plan = plan_cash_equity_trade(
        symbol="infy", entry_price=100, stop_price=98,
        available_cash_rupees=25_000,
    )
    assert plan.approved is True
    assert plan.paper_only is True
    assert plan.symbol == "INFY"
    assert plan.quantity == 50
    assert plan.position_rupees == 5_000
    assert plan.entry_cash_needed_rupees == 5_007.50
    assert plan.estimated_stop_loss_rupees <= 125
    assert plan.daily_loss_limit_rupees == 250


def test_daily_loss_cap_blocks_new_plan():
    plan = plan_cash_equity_trade(
        symbol="INFY", entry_price=100, stop_price=98,
        available_cash_rupees=25_000, daily_realized_pnl_rupees=-250,
    )
    assert not plan.approved
    assert plan.quantity == 0
    assert "Daily loss limit" in plan.reason


def test_remaining_daily_budget_reduces_size():
    plan = plan_cash_equity_trade(
        symbol="INFY", entry_price=100, stop_price=98,
        available_cash_rupees=25_000, daily_realized_pnl_rupees=-225,
    )
    assert plan.approved
    assert plan.estimated_stop_loss_rupees <= 25
    assert plan.quantity <= 10


def test_insufficient_cash_blocks_trade():
    plan = plan_cash_equity_trade(
        symbol="INFY", entry_price=100, stop_price=98,
        available_cash_rupees=50,
    )
    assert not plan.approved


def test_existing_exposure_reduces_remaining_position_budget():
    plan = plan_cash_equity_trade(
        symbol="INFY", entry_price=100, stop_price=98,
        available_cash_rupees=25_000, existing_symbol_exposure_rupees=4_800,
    )
    assert plan.approved
    assert plan.quantity == 2


@pytest.mark.parametrize("stop", [100, 101, 0, -1])
def test_invalid_stop_rejected(stop):
    with pytest.raises(ValueError):
        plan_cash_equity_trade(
            symbol="INFY", entry_price=100, stop_price=stop,
            available_cash_rupees=25_000,
        )


def test_non_finite_values_rejected():
    with pytest.raises(ValueError):
        plan_cash_equity_trade(
            symbol="INFY", entry_price=math.nan, stop_price=90,
            available_cash_rupees=25_000,
        )


def test_plan_endpoint_is_read_only():
    client = TestClient(app)
    result = client.post("/strategy/small-capital/plan", json={
        "symbol": "INFY", "entry_price": 100, "stop_price": 98,
        "available_cash_rupees": 25_000,
    })
    assert result.status_code == 200
    body = result.json()
    assert body["paper_only"] is True
    assert body["approved"] is True
    assert body["quantity"] == 50


def test_plan_endpoint_rejects_invalid_long_entry():
    response = TestClient(app).post("/strategy/small-capital/plan", json={
        "symbol": "INFY", "entry_price": 100, "stop_price": 100,
        "available_cash_rupees": 25_000,
    })
    assert response.status_code == 422


def test_non_mock_orders_disabled_by_default(monkeypatch):
    monkeypatch.delenv("TRADELENS_ALLOW_LIVE_ORDERS", raising=False)
    client = TestClient(app)
    response = client.post("/orders", json={
        "broker": "dhan", "symbol": "1333", "exchange": "NSE_EQ",
        "side": "buy", "quantity": 1, "order_type": "market",
        "product_type": "cnc",
    })
    assert response.status_code == 403
    assert "Live broker orders are disabled" in response.json()["detail"]


def test_webhook_never_uses_a_non_mock_broker():
    client = TestClient(app)
    response = client.post("/webhooks/strategy", json={
        "source": "testing",
        "signal_type": "entry_long",
        "broker": "dhan",
        "payload": {"paper_trade_order": {
            "symbol": "INFY", "exchange": "NSE",
            "side": "buy", "quantity": 1,
            "order_type": "market", "product_type": "cnc",
        }},
    })
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    assert response.json()["executed"] is False
