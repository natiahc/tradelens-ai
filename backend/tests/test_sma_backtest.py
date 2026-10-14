from datetime import date, timedelta

import pytest

from tradelens_ai.services.sma_backtest import (
    DailyBar,
    backtest_sma,
    read_daily_bars,
)


def sample_bars(count=60):
    start = date(2026, 1, 1)
    bars = []
    for i in range(count):
        price = 100.0 if i < 50 else 110.0
        bars.append(DailyBar(
            date=start + timedelta(days=i),
            open=price, high=price * 1.01,
            low=price * 0.99, close=price,
        ))
    return bars


def test_sma_backtest_uses_only_previous_session_data():
    bars = sample_bars(51)
    result = backtest_sma(bars)
    # The only rally occurs in the LAST bar; it cannot generate a trade yet.
    assert result["trades"] == []
    assert result["final_equity_rupees"] == 25_000
    assert result["paper_only"] is True


def test_sma_backtest_sizing_is_constrained_for_small_capital():
    result = backtest_sma(sample_bars(60))
    buys = [trade for trade in result["trades"] if trade["side"] == "buy"]
    assert buys
    assert all(buy["quantity"] * buy["price"] <= 5_000 for buy in buys)
    assert result["open_position_shares"] > 0
    assert result["closed_trades"] == 0


def test_sma_stop_can_trigger_on_intraday_low():
    bars = sample_bars(54)
    stop_day = bars[52]
    bars[52] = DailyBar(
        date=stop_day.date, open=110, high=111, low=95, close=100,
    )
    result = backtest_sma(bars)
    assert any(trade["reason"] == "stop_estimate" for trade in result["trades"])


def test_invalid_bar_rejected():
    with pytest.raises(ValueError):
        DailyBar(date=date(2026, 1, 1), open=100, high=90, low=80, close=100)


def test_csv_must_be_chronological(tmp_path):
    csv_file = tmp_path / "prices.csv"
    csv_file.write_text(
        "Date,Open,High,Low,Close\n"
        "2026-01-02,100,101,99,100\n"
        "2026-01-01,100,101,99,100\n"
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        read_daily_bars(csv_file)
