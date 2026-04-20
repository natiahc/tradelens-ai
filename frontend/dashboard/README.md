# TradeLens AI Dashboard

This is a lightweight frontend dashboard for the current FastAPI backend.

## What it shows

- system health
- registered brokers
- persisted order history
- audit events
- strategy webhook tester

## How to run

### 1. Start the backend

From the `backend` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn tradelens_ai.api:app --reload
```

### 2. Serve the frontend

From the repository root or inside `frontend/dashboard`:

```bash
python3 -m http.server 8080
```

Open:

```text
http://127.0.0.1:8080/frontend/dashboard/
```

### 3. Connect to backend

Set API Base URL in the dashboard to:

```text
http://127.0.0.1:8000
```

## Notes

If the browser blocks requests, enable CORS in the backend as the next improvement.
