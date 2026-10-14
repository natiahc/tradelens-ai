from __future__ import annotations

"""Owner-only Dhan individual OAuth consent + read-only account connectivity.

Only our own authenticated backend calls Dhan endpoints. The AI never sees
the API key, API secret, one-time token ID, or access token.
"""

import hashlib
import os
import secrets
import sqlite3
import time
from urllib.parse import urlencode

import httpx

from tradelens_ai.brokers.dhan_client import DhanApiClient
from tradelens_ai.services.broker_credentials_service import BrokerCredentialsService


class DhanConnectionError(ValueError):
    """A safe error suitable for a user-facing configuration message."""


def _require_credentials(service: BrokerCredentialsService) -> dict[str, str]:
    if not os.getenv("TRADELENS_MASTER_KEY", "").strip():
        raise DhanConnectionError("Set a persistent TRADELENS_MASTER_KEY on Render first.")
    values = service.reveal_secrets()
    if str(values.get("broker_name", "")).lower() != "dhan":
        raise DhanConnectionError("Choose Dhan in Broker Credentials before connecting.")
    if not all(values.get(field) for field in ("client_id", "api_key", "api_secret")):
        raise DhanConnectionError("Enter Dhan client ID, API key and API secret in secure Broker Credentials.")
    return values


class DhanConnectionService:
    CONSENT_API = "https://auth.dhan.co/app/generate-consent"
    CONSUME_API = "https://auth.dhan.co/app/consumeApp-consent"
    LOGIN_PAGE = "https://auth.dhan.co/login/consentApp-login"

    def __init__(self, db_path: str, credentials: BrokerCredentialsService):
        self.db_path = db_path
        self.credentials = credentials
        with sqlite3.connect(self.db_path, timeout=5) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS dhan_oauth_flows (
                    flow_hash TEXT PRIMARY KEY,
                    issued_at INTEGER NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0
                )
            """)

    def start(self) -> dict:
        values = _require_credentials(self.credentials)
        try:
            with httpx.Client(timeout=12, follow_redirects=False) as client:
                response = client.post(
                    self.CONSENT_API,
                    params={"client_id": values["client_id"]},
                    headers={"app_id": values["api_key"], "app_secret": values["api_secret"]},
                )
                response.raise_for_status()
                data = response.json()
            consent = str(data.get("consentAppId") or "")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise DhanConnectionError("Dhan consent request failed. Check the app credentials and try again.") from None
        if not consent or len(consent) > 256:
            raise DhanConnectionError("Dhan did not provide a consent session.")
        state = secrets.token_urlsafe(32)
        digest = hashlib.sha256(state.encode()).hexdigest()
        with sqlite3.connect(self.db_path, timeout=5) as con:
            con.execute("DELETE FROM dhan_oauth_flows WHERE issued_at < ?", (int(time.time()) - 3600,))
            con.execute("INSERT INTO dhan_oauth_flows (flow_hash, issued_at) VALUES (?,?)",
                        (digest, int(time.time())))
        return {
            "login_url": self.LOGIN_PAGE + "?" + urlencode({"consentAppId": consent}),
            "flow_state": state,
            "message": "Finish login and 2FA on Dhan's official site. No trade will be placed.",
        }

    def complete(self, state: str, token_id: str) -> dict:
        if not (10 <= len(state) <= 128 and 1 <= len(token_id) <= 2048):
            raise DhanConnectionError("Invalid or expired Dhan connection callback.")
        digest = hashlib.sha256(state.encode()).hexdigest()
        with sqlite3.connect(self.db_path, timeout=5) as con:
            update = con.execute(
                "UPDATE dhan_oauth_flows SET used=1 "
                "WHERE flow_hash=? AND used=0 AND issued_at>=?",
                (digest, int(time.time()) - 600),
            )
            if update.rowcount != 1:
                raise DhanConnectionError("Dhan login session expired or was already used. Connect again.")
        values = _require_credentials(self.credentials)
        try:
            with httpx.Client(timeout=12, follow_redirects=False) as client:
                response = client.get(
                    self.CONSUME_API,
                    params={"tokenId": token_id},
                    headers={"app_id": values["api_key"], "app_secret": values["api_secret"]},
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError, TypeError):
            raise DhanConnectionError("Dhan did not approve this connection. Start a new login.") from None
        access_token = str(data.get("accessToken") or "")
        returned_client_id = str(data.get("dhanClientId") or "")
        if not access_token or not secrets.compare_digest(returned_client_id, values["client_id"]):
            raise DhanConnectionError("Dhan login response did not match the configured account.")
        self.credentials.update_profile(
            broker_name="dhan",
            client_id=values["client_id"],
            api_key=values["api_key"],
            access_token=access_token,
            api_secret=values["api_secret"],
        )
        return {
            "connected": True, "broker": "dhan",
            "expires_at": str(data.get("expiryTime") or "Check Dhan token validity"),
            "message": "Dhan is connected for read-only account viewing. Trading remains disabled.",
        }

    def overview(self, category: str) -> dict:
        if category not in {"funds", "holdings", "positions", "orders", "profile"}:
            raise DhanConnectionError("Use one of: funds, holdings, positions, orders, profile.")
        values = _require_credentials(self.credentials)
        if not values.get("access_token"):
            raise DhanConnectionError("Connect Dhan or enter a Dhan access token first.")
        client = DhanApiClient(
            client_id=values["client_id"],
            access_token=values["access_token"],
            base_url="https://api.dhan.co/v2",
        )
        try:
            if category == "funds":
                rows = client.get_funds()
            elif category == "holdings":
                rows = client.get_holdings()
            elif category == "positions":
                rows = client.get_positions()
            elif category == "orders":
                rows = client.get_orders()
            else:
                rows = client._request("GET", "/profile")
        except Exception:
            # The legacy client can include provider bodies in exceptions.
            # Do not echo them into chat logs or HTTP responses.
            raise DhanConnectionError(
                "Dhan account data could not be fetched. Check token validity and API permissions."
            ) from None
        # Explicit read-only result. Do not include credentials or raw headers.
        if isinstance(rows, dict):
            data = rows.get("data", rows)
        else:
            data = rows
        if isinstance(data, list):
            # Bound response size; raw full portfolio fetch stays a separate explicit user request.
            data = data[:100]
        return {
            "broker": "dhan", "category": category, "read_only": True,
            "data": data,
            "notice": "This response contains private account data. It is not sent to the AI model.",
        }
