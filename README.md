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
