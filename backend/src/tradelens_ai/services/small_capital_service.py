from __future__ import annotations

"""Paper-only position sizing for small Indian cash-equity accounts.

This module NEVER submits orders. The supplied prices and daily P&L are inputs
from the caller, not verified market/account data.
"""

from dataclasses import asdict, dataclass
import math
import re


@dataclass(frozen=True, slots=True)
class SmallCapitalLimits:
    capital_rupees: float = 25_000.0
    risk_per_trade_pct: float = 0.005   # 0.5% of starting capital
    daily_loss_limit_pct: float = 0.01  # 1% of starting capital
    max_position_pct: float = 0.20     # 20% of starting capital
    estimated_cost_per_side_pct: float = 0.0015  # illustrative, not a broker tariff


@dataclass(frozen=True, slots=True)
class TradePlan:
    approved: bool
    reason: str
    symbol: str
    quantity: int
    entry_price: float
    stop_price: float
    position_rupees: float
    entry_cash_needed_rupees: float
    estimated_stop_loss_rupees: float
    daily_loss_limit_rupees: float
    remaining_daily_risk_rupees: float
    paper_only: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def plan_cash_equity_trade(
    *,
    symbol: str,
    entry_price: float,
    stop_price: float,
    available_cash_rupees: float,
    daily_realized_pnl_rupees: float = 0.0,
    existing_symbol_exposure_rupees: float = 0.0,
    limits: SmallCapitalLimits | None = None,
) -> TradePlan:
    """Size a hypothetical long-only NSE CNC trade without placing an order.

    The estimated stop loss includes illustrative entry/exit costs. Actual fills
    can gap through a stop, so this estimate is NOT a guaranteed maximum loss.
    The daily loss check is advisory until connected to verified broker P&L.
    """
    limits = limits or SmallCapitalLimits()
    symbol = symbol.strip().upper()

    values = (
        entry_price, stop_price, available_cash_rupees,
        daily_realized_pnl_rupees, existing_symbol_exposure_rupees,
        limits.capital_rupees, limits.risk_per_trade_pct,
        limits.daily_loss_limit_pct, limits.max_position_pct,
        limits.estimated_cost_per_side_pct,
    )
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("All financial inputs must be finite numbers")
    if not re.fullmatch(r"[A-Z][A-Z0-9&.-]{0,24}", symbol):
        raise ValueError("Use an NSE cash-equity symbol, e.g. INFY")
    if entry_price <= 0 or stop_price <= 0 or stop_price >= entry_price:
        raise ValueError("A long entry requires 0 < stop_price < entry_price")
    if available_cash_rupees < 0 or existing_symbol_exposure_rupees < 0:
        raise ValueError("Cash and existing exposure must not be negative")
    if limits.capital_rupees <= 0:
        raise ValueError("Starting capital must be positive")
    if not (0 < limits.risk_per_trade_pct <= 1):
        raise ValueError("risk_per_trade_pct must be in (0, 1]")
    if not (0 < limits.daily_loss_limit_pct <= 1):
        raise ValueError("daily_loss_limit_pct must be in (0, 1]")
    if not (0 < limits.max_position_pct <= 1):
        raise ValueError("max_position_pct must be in (0, 1]")
    if not (0 <= limits.estimated_cost_per_side_pct < 1):
        raise ValueError("estimated_cost_per_side_pct must be in [0, 1)")

    daily_limit = limits.capital_rupees * limits.daily_loss_limit_pct
    remaining_daily_risk = max(0.0, daily_limit + min(daily_realized_pnl_rupees, 0.0))

    def rejected(reason: str) -> TradePlan:
        return TradePlan(
            approved=False, reason=reason, symbol=symbol, quantity=0,
            entry_price=entry_price, stop_price=stop_price,
            position_rupees=0.0, entry_cash_needed_rupees=0.0,
            estimated_stop_loss_rupees=0.0,
            daily_loss_limit_rupees=round(daily_limit, 2),
            remaining_daily_risk_rupees=round(remaining_daily_risk, 2),
        )

    if remaining_daily_risk <= 0:
        return rejected("Daily loss limit reached; no new positions")
    if available_cash_rupees <= 0:
        return rejected("No available cash for a new position")

    cost = limits.estimated_cost_per_side_pct
    risk_per_share = (entry_price - stop_price) + cost * (entry_price + stop_price)
    budget_risk = min(limits.capital_rupees * limits.risk_per_trade_pct, remaining_daily_risk)
    remaining_position_budget = max(
        0.0, limits.capital_rupees * limits.max_position_pct - existing_symbol_exposure_rupees
    )
    quantity = min(
        math.floor(budget_risk / risk_per_share),
        math.floor(remaining_position_budget / entry_price),
        math.floor(available_cash_rupees / (entry_price * (1 + cost))),
    )
    if quantity < 1:
        return rejected("Insufficient budget for one share within risk limits")

    position = quantity * entry_price
    return TradePlan(
        approved=True,
        reason="Paper plan only; no order was placed",
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        stop_price=stop_price,
        position_rupees=round(position, 2),
        entry_cash_needed_rupees=round(position * (1 + cost), 2),
        estimated_stop_loss_rupees=round(quantity * risk_per_share, 2),
        daily_loss_limit_rupees=round(daily_limit, 2),
        remaining_daily_risk_rupees=round(remaining_daily_risk, 2),
    )
