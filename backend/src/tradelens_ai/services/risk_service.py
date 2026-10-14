from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from tradelens_ai.persistence.sqlite_store import SQLiteStore
from tradelens_ai.services.risk_settings_service import RiskSettingsService


@dataclass(slots=True)
class RiskDecision:
    allowed: bool
    reason: str


class StrategyRiskService:
    def __init__(self, audit_store: SQLiteStore, risk_settings_service: RiskSettingsService) -> None:
        self._audit_store = audit_store
        self._risk_settings_service = risk_settings_service

    def evaluate(self, *, broker_name: str | None, payload: dict[str, Any]) -> RiskDecision:
        settings = self._risk_settings_service.get_settings()

        if broker_name is None:
            return RiskDecision(False, "Broker is required for strategy execution")

        # Signals named "paper_trade_order" must never reach a live broker.
        if broker_name != "mock":
            return RiskDecision(False, "Automated strategy webhooks are paper-only (mock broker)")

        if broker_name not in set(settings.allowed_brokers):
            return RiskDecision(False, f"Broker not allowed for strategy execution: {broker_name}")

        order_payload = payload.get("paper_trade_order")
        if not isinstance(order_payload, dict):
            return RiskDecision(True, "No executable paper_trade_order found")

        symbol = str(order_payload.get("symbol", "")).upper()
        if symbol not in set(settings.allowed_symbols):
            return RiskDecision(False, f"Symbol not allowed for execution: {symbol}")

        try:
            quantity = int(order_payload.get("quantity", 0))
        except (TypeError, ValueError):
            return RiskDecision(False, "Quantity must be a positive integer")
        if quantity <= 0:
            return RiskDecision(False, "Quantity must be greater than zero")
        if quantity > settings.max_quantity:
            return RiskDecision(False, f"Quantity exceeds max limit: {quantity} > {settings.max_quantity}")

        if self._strategy_execution_count_today() >= settings.max_daily_strategy_executions:
            return RiskDecision(False, "Daily strategy execution limit reached")

        return RiskDecision(True, "Risk checks passed")

    def _strategy_execution_count_today(self) -> int:
        events = self._audit_store.list_audit_events(limit=1000)
        today_utc = datetime.now(timezone.utc).date().isoformat()
        return sum(
            1 for event in events
            if event.event_type == "strategy_signal_executed"
            and event.created_at[:10] == today_utc
        )
