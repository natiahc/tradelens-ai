# Small-capital paper trading (research mode)

This is a conservative **research workflow**, not an automatic income system.
TradeLens defaults to a simulated ₹25,000 account; no account funding,
API token or broker connection is required. No guarantee of daily profit.

## Built-in sizing limits

- Starting capital: ₹25,000 (adjustable per request)
- Estimated risk per trade: 0.5% of starting capital (₹125)
- Loss threshold for the day: 1% of starting capital (₹250)
- Maximum exposure per symbol: 20% of starting capital (₹5,000)
- Estimated transaction cost: 0.15% of notional **per side**, for modelling only
- Long-only NSE cash-equity assumptions (CNC); no leverage or derivatives
- The planner is **read-only**. It never calls a broker.

The daily-P&L and available-cash numbers are supplied by the caller and are
**not verified with broker accounts**. Therefore these are modelling safeguards,
not production risk enforcement. In particular, a stop may fill below its price
during a gap; the quoted loss is only an estimate.

## 1. Install on Ubuntu

```bash
git clone https://github.com/natiahc/tradelens-ai.git
cd tradelens-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Once the repository is private, cloning requires GitHub authentication.

## 2. Request a paper trade plan

Run the API:

```bash
uvicorn tradelens_ai.api:app --reload --host 127.0.0.1
```

In a second terminal:

```bash
curl -s -X POST http://127.0.0.1:8000/strategy/small-capital/plan \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "INFY",
    "entry_price": 100,
    "stop_price": 98,
    "available_cash_rupees": 25000,
    "daily_realized_pnl_rupees": 0,
    "existing_symbol_exposure_rupees": 0,
    "capital_rupees": 25000
  }'
```

The result gives hypothetical quantity, cash required, approximate loss if
the stop filled, and the remaining daily loss budget. Example input prices
above are illustrative, **not live INFY market prices**.

To test the daily stop, use `"daily_realized_pnl_rupees": -250`; the
planner should reject a new position.

## 3. Backtest a basic 20/50-day SMA strategy

Export historical **unadjusted daily OHLC** data from an appropriately licensed
data provider as an ascending CSV:

```csv
Date,Open,High,Low,Close
2026-01-01,100,101,99,100
2026-01-02,101,102,100,101
```

The two example rows are not enough; the default test needs **51+ sessions**.
Use real, continuous market sessions with consistent prices. Do not mix
adjusted close prices with unadjusted OHLC values.

```bash
python -m tradelens_ai.services.sma_backtest \
  --csv /path/to/infy_daily.csv \
  --symbol INFY --capital 25000 --fast 20 --slow 50 --stop-pct 0.02
```

The backtest:
- makes decisions using **yesterday's closing data**
- buys or exits at the **next day's opening price**
- allocates positions through the paper-only sizing function
- estimates stop exits from daily lows (conservatively models opening gaps)
- reports trades, total return, max drawdown, and open position
- uses simplified proportional fees; these must be replaced with exact broker
  fees, exchange levies, taxes and observed slippage before relying on results

Limitations: no dividends, split adjustments, exact fill simulation,
intraday stop ordering, regulatory or broker limits, delayed data, survivorship
bias controls, walk-forward tuning or broker reconciliation. This is a research
baseline, **not a production-ready algorithm or proven profitable strategy**.

## 4. Live trading remains disabled by default

The strategy webhook now allows only the `mock` broker. Direct `POST /orders`
calls to non-mock brokers return HTTP 403 by default. A separate
`TRADELENS_ALLOW_LIVE_ORDERS=true` setting exists for future work, but **do
not enable it on the current public-facing backend**: the app does not yet
implement the authentication, authorization, idempotency, trade-state
reconciliation or kill-switch controls required for safe production execution.

**Important:** Making the GitHub repository private does **not** make a
deployed Vercel frontend or Render API private, or revoke keys already exposed
in older Git history. Keep real broker credentials out of the deployed API
until it is secured.

## 5. Readiness gates before any real money

Obtain broker-compliant market data and API access, implement and verify
actual cost calculation, walk-forward/backtest and paper-trade for several
weeks, secure authentication, replay protection, kill switch, and live
broker-verified P&L / order state. Verify applicable SEBI/exchange broker API
requirements and ensure you can afford a total loss of the trading capital.
