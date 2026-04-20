from __future__ import annotations

from dataclasses import dataclass

from tradelens_ai.persistence.sqlite_store import SQLiteStore


@dataclass(slots=True)
class StrategySummary:
    signals_received: int
    executed: int
    blocked: int
    skipped: int


class StrategySummaryService:
    def __init__(self, audit_store: SQLiteStore) -> None:
        self._audit_store = audit_store

    def get_summary(self) -> StrategySummary:
        events = self._audit_store.list_audit_events(limit=5000)
        received = 0
        executed = 0
        blocked = 0
        skipped = 0

        for event in events:
            if event.event_type == "strategy_signal_received":
                received += 1
            elif event.event_type == "strategy_signal_executed":
                executed += 1
            elif event.event_type == "strategy_signal_blocked":
                blocked += 1
            elif event.event_type == "strategy_signal_skipped":
                skipped += 1

        return StrategySummary(
            signals_received=received,
            executed=executed,
            blocked=blocked,
            skipped=skipped,
        )
