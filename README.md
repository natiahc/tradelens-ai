# TradeLens AI

TradeLens AI is a multi-broker trading intelligence and algorithmic execution platform designed for Indian markets.

## Vision

Build a unified platform that can connect to multiple brokers such as Groww, Dhan, and Zerodha while providing:

- normalized broker APIs for orders, positions, holdings, and market data
- paper trading and live execution workflows
- risk controls, audit logs, and operational safety
- AI-assisted trade journaling and performance analytics
- ML/DL-based signal scoring and market regime detection

## Why this project

Indian traders increasingly use broker APIs, but the ecosystem is fragmented. Each broker differs in authentication, rate limits, symbols, order semantics, market data interfaces, and operational constraints. TradeLens AI aims to provide one consistent platform above those differences.

## Product direction

### Phase 1
- broker connectivity
- normalized domain model
- paper trading
- execution dashboard
- audit logging

### Phase 2
- risk engine
- webhook and strategy runtime
- P&L and slippage analytics
- alerting and notifications

### Phase 3
- AI trade journal
- ML signal ranking
- regime classification
- execution intelligence and recommendations

## Initial architecture

- frontend/web-app
- backend/api-gateway
- backend/auth-service
- backend/broker-service
- backend/execution-service
- backend/portfolio-service
- backend/risk-service
- backend/market-data-service
- backend/strategy-service
- backend/ai-insights-service
- docs/

## Principles

- safety before automation
- modularity before scale
- observability from day one
- AI as decision support, not magic

## Current backend structure

- `backend/src/tradelens_ai/domain/` normalized trading models
- `backend/src/tradelens_ai/brokers/` broker abstraction and adapters
- `backend/src/tradelens_ai/api/` FastAPI app, schemas, and mappers

## Running the backend

### 1. Create a virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Run the demo script

```bash
tradelens-demo
```

### 4. Run the API server

```bash
uvicorn tradelens_ai.api:app --reload
```

## Current API endpoints

- `GET /health`
- `GET /brokers`
- `POST /orders`
- `GET /orders/{broker_name}`
- `GET /positions/{broker_name}`
- `GET /holdings/{broker_name}`
- `GET /funds/{broker_name}`

## Current status

The repository now includes architecture docs, a backend package scaffold, a normalized broker layer, a mock broker adapter, real API endpoints, and broker adapter skeletons for Dhan, Zerodha, and Groww.


## Small-capital algo research (paper only)

TradeLens now includes a **₹25,000 default simulated-account** trade planner and
an offline 20/50-day SMA backtester. The paper planner caps estimated risk per
trade (0.5%), daily loss (1%) and single-position exposure (20%). These are
research defaults, not a source of guaranteed income.

- `POST /strategy/small-capital/plan`: calculate a hypothetical NSE equity
  position; **never** sends an order.
- `python -m tradelens_ai.services.sma_backtest --csv /path/to/prices.csv`:
  run the historical CSV backtest (requires daily OHLC data).
- Automated webhook orders are restricted to the `mock` broker.
- Direct live broker orders are disabled by default, and the app still lacks
  production-ready authentication.

See [the complete small-capital guide](docs/small_capital.md) for examples,
known limitations, testing steps and mandatory production safety work.


## Ask TradeLens (guided in-app assistant)

The existing Vercel dashboard includes a floating **Ask TradeLens** chat window.
Ask `How do I use this app?` for a step-by-step walkthrough; change safe
local paper settings (capital, SMA windows, stops and dashboard layout), or
describe a feature and select **Save request** to queue development work.

The assistant is **not** a live order executor or an autonomous coding agent.
Optional Ollama/OpenAI models provide richer replies when connected to the
existing Render backend; guided mode requires no AI model.

Full setup, supported commands and security limits:
[TradeLens Assistant guide](docs/tradelens_assistant.md).
