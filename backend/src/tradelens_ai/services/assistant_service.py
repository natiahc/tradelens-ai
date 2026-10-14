from __future__ import annotations

"""Authenticated advisory chat for TradeLens AI.

This service proposes changes; it cannot edit GitHub, deploy, or trade.
AI is optional: OpenAI or a reachable Ollama endpoint may supply richer replies.
"""

import os
import re
import sqlite3
from urllib.parse import urlsplit
from datetime import datetime, timezone

import httpx


SECRET_PATTERN = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{15,}|(?:api[_ -]?key|access[_ -]?token|"
    r"refresh[_ -]?token|password|client[_ -]?secret)\s*[:=]\s*\S{8,})"
)

ASSISTANT_CONTEXT = """You are TradeLens Assistant for the user's TradeLens AI project.
Architecture: plain JS/CSS/HTML dashboard on existing Vercel project,
FastAPI Python backend on existing Render service, SQLite persistence.
Features: diagnostic status/logs, mock broker, paper position sizing,
CSV-based 20/50 SMA backtesting, admin-token-protected operational APIs.
Your scope: explain how features work, troubleshoot visible errors, make an
ordered safe implementation plan for requested app changes, and suggest
the next UI action. You DO NOT have code-editing tools, repository write
permissions, broker order tools, or deploy permissions in this chat.
Never claim you changed code or executed trades. Never promise daily returns.
For changes to actual code, advise saving a feature request for developer review.
Only paper-research browser settings can be changed by deterministic local
commands, with user confirmation when relevant.
No financial advice, no credentials, no API keys, no live-trading enablement.
Be precise and concise (at most about 170 words per answer).
"""


def contains_secret(text: str) -> bool:
    return bool(SECRET_PATTERN.search(text))


def guided_reply(message: str) -> str:
    question = message.casefold()
    if any(term in question for term in ("how to use", "how do i use", "how can i use", "guide me", "getting started", "how this app works", "how to start", "tutorial")):
        return (
            "Here's how to use TradeLens AI:\\n"
            "1. In Small Capital Lab, choose a simulated budget (for example ₹25,000).\\n"
            "2. Enter an illustrative entry/stop price and click Calculate Paper Position.\\n"
            "3. Upload daily OHLC prices in Date,Open,High,Low,Close format, "
            "or load the synthetic demo (not actual prices).\\n"
            "4. Run Paper Backtest and examine fees, return, max drawdown and trades.\\n"
            "5. Check Audit & Diagnostics for health and API coverage.\\n"
            "6. Ask the assistant to change paper settings or save a feature request.\\n"
            "No automatic live orders or guaranteed earnings."
        )
    if any(term in question for term in ("daily money", "daily profit", "guarantee", "income")):
        return (
            "TradeLens cannot guarantee daily earnings. Start with paper trading, "
            "compare net returns after fees, inspect maximum drawdown, and validate "
            "on out-of-sample market data. Save a feature request if you want "
            "daily P&L charts or a performance report added to the dashboard."
        )
    if any(term in question for term in ("error", "logs", "audit", "debug", "not working")):
        return (
            "Open Audit & Diagnostics and select Run Diagnostics. Save an admin "
            "audit after unlocking tools if you need persistent backend checks. "
            "Export sanitized logs for development. Server logs from Render and "
            "deployment logs from Vercel require their authenticated consoles."
        )
    if any(term in question for term in ("broker", "upstox", "zerodha", "dhan", "groww", "api")):
        return (
            "The app has mock-broker research and some broker adapters, but no "
            "production-safe automatic trading. A new broker integration needs "
            "an authenticated backend adapter, tests, order reconciliation, "
            "trade limits and regulator/broker checks. Save this as a feature "
            "request to make it actionable."
        )
    if any(term in question for term in ("strategy", "ema", "rsi", "backtest", "indicator")):
        return (
            "Use Small Capital Lab to upload consistent daily OHLC data, "
            "set SMA parameters, and run a paper backtest. A new indicator "
            "requires strategy code, tests against known data, transaction-cost "
            "estimates and walk-forward validation. Save your exact rules as "
            "a feature request."
        )
    if any(term in question for term in ("design", "layout", "mobile", "color", "theme", "ui")):
        return (
            "I can help define your dashboard design change. Include the section, "
            "desired appearance, mobile behavior and examples. Select Save Request "
            "to store the proposed change for development. Browser-only paper "
            "settings can be changed instantly through chat commands."
        )
    return (
        "I can guide your TradeLens changes. Try 'Set capital to 30000', "
        "'Set fast MA to 15', 'Run diagnostics' or 'Show supported APIs'. "
        "For features requiring code updates, describe the behavior, then "
        "select Save Request. Saving a request does not automatically deploy code."
    )


def _ollama_reply(messages: list[dict[str, str]]) -> str:
    """Connect to a configured Ollama service, never a browser-submitted URL."""
    base = os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if not base or not model:
        raise ValueError("Ollama endpoint or model is not configured")
    parts = urlsplit(base)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
        raise ValueError("OLLAMA_BASE_URL must be a valid HTTP(S) service endpoint")
    headers = {"Content-Type": "application/json"}
    key = os.getenv("OLLAMA_API_KEY", "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    with httpx.Client(timeout=18, follow_redirects=False) as client:
        response = client.post(
            base + "/api/chat",
            headers=headers,
            json={
                "model": model,
                "stream": False,
                "messages": [{"role": "system", "content": ASSISTANT_CONTEXT}] + messages,
                "options": {"num_predict": 450, "temperature": 0.3},
            },
        )
        response.raise_for_status()
    return str(response.json().get("message", {}).get("content", "")).strip()[:3500]


def _openai_reply(messages: list[dict[str, str]]) -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("No OpenAI key configured")
    model = os.getenv("TRADELENS_CHAT_MODEL", "gpt-4.1-mini").strip()
    with httpx.Client(timeout=18, follow_redirects=False) as client:
        response = client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "instructions": ASSISTANT_CONTEXT,
                "input": messages,
                "max_output_tokens": 450,
                "store": False,
            },
        )
        response.raise_for_status()
    chunks = [
        piece.get("text", "")
        for output in response.json().get("output", [])
        if output.get("type") == "message"
        for piece in output.get("content", [])
        if piece.get("type") == "output_text"
    ]
    return "\\n".join(x for x in chunks if x).strip()[:3500]


def advisory_reply(message: str, history: list[dict[str, str]]) -> tuple[str, str]:
    """Return (reply, mode) without executing code, changing settings or trading."""
    if contains_secret(message) or any(contains_secret(row.get("content", "")) for row in history):
        raise ValueError("Remove API keys, access tokens or passwords from chat messages")

    selected = [
        {"role": row["role"], "content": row["content"][:1500]}
        for row in history[-8:]
        if row.get("role") in {"user", "assistant"} and isinstance(row.get("content"), str)
    ]
    selected.append({"role": "user", "content": message[:2000]})
    preference = os.getenv("TRADELENS_CHAT_PROVIDER", "auto").strip().lower()
    # Explicit opt-out prevents uploading any chat text to external AI services.
    if preference not in {"auto", "ollama", "openai", "guided"}:
        preference = "guided"

    providers = (
        ["ollama", "openai"] if preference == "auto" else
        [preference] if preference != "guided" else []
    )
    for provider in providers:
        try:
            answer = (_ollama_reply(selected) if provider == "ollama"
                      else _openai_reply(selected))
            if answer:
                return answer, provider
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            # Fail gracefully without revealing endpoint keys or provider errors.
            continue

    return guided_reply(message), "guided"


class ChangeRequestStore:
    """Bounded SQLite requests. Requires admin authentication at API layer."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        with sqlite3.connect(db_path, timeout=5) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assistant_change_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TEXT NOT NULL
                )
            """)

    def save(self, description: str) -> dict:
        description = description.strip()
        if not 5 <= len(description) <= 2000:
            raise ValueError("Request must contain 5–2000 characters")
        if contains_secret(description):
            raise ValueError("Do not include credentials or tokens in saved requests")
        timestamp = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self._db_path, timeout=5) as conn:
            cursor = conn.execute(
                "INSERT INTO assistant_change_requests (description, status, created_at) "
                "VALUES (?, 'proposed', ?)", (description, timestamp)
            )
            request_id = cursor.lastrowid
        return {
            "request_id": int(request_id),
            "description": description,
            "status": "proposed",
            "created_at": timestamp,
        }

    def list_requests(self, limit: int = 30) -> list[dict]:
        with sqlite3.connect(self._db_path, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT request_id, description, status, created_at "
                "FROM assistant_change_requests ORDER BY request_id DESC LIMIT ?",
                (max(1, min(limit, 50)),),
            ).fetchall()
        return [dict(row) for row in rows]
