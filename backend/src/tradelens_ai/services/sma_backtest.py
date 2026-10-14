from __future__ import annotations

"""Offline, long-only SMA research backtest. No market API or broker orders.

Signals use only closes from PREVIOUS sessions and orders are modelled at
the NEXT session's open. Stops use daily OHLC bars, so fills are only estimates.
This is NOT a production execution engine.
"""

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import date
import json
import math
from pathlib import Path

from tradelens_ai.services.small_capital_service import (
    SmallCapitalLimits,
    plan_cash_equity_trade,
)


@dataclass(frozen=True, slots=True)
class DailyBar:
    date: date
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        prices = (self.open, self.high, self.low, self.close)
        if any(not math.isfinite(price) or price <= 0 for price in prices):
            raise ValueError("OHLC values must be finite and positive")
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError("OHLC bar has inconsistent high/low")
        if self.high < self.low:
            raise ValueError("Bar high must be >= low")


def read_daily_bars(path: str | Path) -> list[DailyBar]:
    """Load an ascending Date,Open,High,Low,Close CSV with no adjusted-price mixing."""
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        for row in csv.DictReader(csv_file):
            bars.append(DailyBar(
                date=date.fromisoformat(row["Date"]),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
            ))
    if any(previous.date >= current.date for previous, current in zip(bars, bars[1:])):
        raise ValueError("CSV dates must be strictly increasing, with no duplicate days")
    return bars


def backtest_sma(
    bars: list[DailyBar],
    *,
    symbol: str = "INFY",
    limits: SmallCapitalLimits | None = None,
    fast_days: int = 20,
    slow_days: int = 50,
    stop_pct: float = 0.02,
) -> dict:
    """Test long-only cash equity with entry sizing and stop-loss estimation."""
    limits = limits or SmallCapitalLimits()
    if fast_days <= 0 or slow_days <= fast_days:
        raise ValueError("Require 0 < fast_days < slow_days")
    if len(bars) <= slow_days:
        raise ValueError("Need more OHLC sessions than the slow MA window")
    if not (0 < stop_pct < 1):
        raise ValueError("stop_pct must be in (0, 1)")
    if any(a.date >= b.date for a, b in zip(bars, bars[1:])):
        raise ValueError("Bars must be in chronological order")

    closes = [bar.close for bar in bars]
    cash = limits.capital_rupees
    quantity = 0
    cost_basis = 0.0  # price plus entry fees for existing position
    stop_price = 0.0
    trades = []
    peak_equity = cash
    max_drawdown = 0.0
    costs = limits.estimated_cost_per_side_pct
    equity_curve = []

    for index, bar in enumerate(bars):
        if index < slow_days:
            equity_curve.append(round(cash, 2))
            continue

        # At session open, only close prices up to YESTERDAY are available.
        fast_ma = sum(closes[index - fast_days:index]) / fast_days
        slow_ma = sum(closes[index - slow_days:index]) / slow_days
        wants_long = fast_ma > slow_ma

        if quantity and not wants_long:
            proceeds = quantity * bar.open * (1 - costs)
            trades.append({
                "date": bar.date.isoformat(),
                "side": "sell", "quantity": quantity,
                "price": round(bar.open, 2), "reason": "sma_exit",
                "realized_pnl_rupees": round(proceeds - cost_basis, 2),
            })
            cash += proceeds
            quantity = 0
            cost_basis = 0.0
            stop_price = 0.0

        if not quantity and wants_long:
            plan = plan_cash_equity_trade(
                symbol=symbol, entry_price=bar.open,
                stop_price=bar.open * (1 - stop_pct),
                available_cash_rupees=cash, limits=limits,
            )
            if plan.approved:
                quantity = plan.quantity
                stop_price = plan.stop_price
                cost_basis = quantity * bar.open * (1 + costs)
                cash -= cost_basis
                trades.append({
                    "date": bar.date.isoformat(),
                    "side": "buy", "quantity": quantity,
                    "price": round(bar.open, 2), "reason": "sma_entry",
                })

        # If the stop was touched, assume a stop fill; opening gaps fill worse.
        # Intraday bar ordering and actual stop execution are UNKNOWN.
        if quantity and bar.low <= stop_price:
            fill = min(stop_price, bar.open)
            proceeds = quantity * fill * (1 - costs)
            trades.append({
                "date": bar.date.isoformat(),
                "side": "sell", "quantity": quantity,
                "price": round(fill, 2), "reason": "stop_estimate",
                "realized_pnl_rupees": round(proceeds - cost_basis, 2),
            })
            cash += proceeds
            quantity = 0
            cost_basis = 0.0
            stop_price = 0.0

        equity = cash + quantity * bar.close
        peak_equity = max(peak_equity, equity)
        max_drawdown = min(max_drawdown, equity / peak_equity - 1)
        equity_curve.append(round(equity, 2))

    # Open position is marked to market, not forcibly liquidated.
    final_equity = cash + quantity * bars[-1].close
    sell_trades = [trade for trade in trades if trade["side"] == "sell"]
    return {
        "paper_only": True,
        "symbol": symbol,
        "first_date": bars[0].date.isoformat(),
        "last_date": bars[-1].date.isoformat(),
        "initial_capital_rupees": round(limits.capital_rupees, 2),
        "final_equity_rupees": round(final_equity, 2),
        "total_return_pct": round((final_equity / limits.capital_rupees - 1) * 100, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "closed_trades": len(sell_trades),
        "winning_closed_trades": sum(1 for trade in sell_trades if trade["realized_pnl_rupees"] > 0),
        "open_position_shares": quantity,
        "trades": trades,
        "equity_curve": equity_curve,
        "assumptions": [
            "Signals at prior session close; orders at next session open",
            "Estimated proportional entry/exit costs, not actual Indian taxes and fees",
            "Stop fills are approximations and can be worse during gaps",
            "No corporate actions, dividends, borrow, or intraday order book modelling",
            "Historical results do not predict future profits",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TradeLens paper-only small-account SMA backtest")
    parser.add_argument("--csv", required=True, help="CSV containing Date,Open,High,Low,Close")
    parser.add_argument("--symbol", default="INFY")
    parser.add_argument("--capital", type=float, default=25_000.0)
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=50)
    parser.add_argument("--stop-pct", type=float, default=0.02)
    args = parser.parse_args()

    result = backtest_sma(
        read_daily_bars(args.csv),
        symbol=args.symbol,
        limits=SmallCapitalLimits(capital_rupees=args.capital),
        fast_days=args.fast, slow_days=args.slow, stop_pct=args.stop_pct,
    )
    print(json.dumps({key: value for key, value in result.items() if key != "equity_curve"}, indent=2))


if __name__ == "__main__":
    main()
