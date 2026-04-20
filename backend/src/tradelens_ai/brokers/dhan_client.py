from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class DhanApiError(RuntimeError):
    pass


@dataclass(slots=True)
class DhanApiClient:
    client_id: str
    access_token: str
    base_url: str = "https://api.dhan.co"
    timeout_seconds: float = 15.0

    ORDERS_PATH: str = "/orders"
    POSITIONS_PATH: str = "/positions"
    HOLDINGS_PATH: str = "/holdings"
    FUNDS_PATH: str = "/fundlimit"

    def auth_headers(self) -> dict[str, str]:
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def build_url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def _request(self, method: str, path: str, *, json_body: dict[str, Any] | None = None) -> dict | list:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.request(
                    method=method,
                    url=self.build_url(path),
                    headers=self.auth_headers(),
                    json=json_body,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            raise DhanApiError(f"Dhan API HTTP error {exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise DhanApiError(f"Dhan API network error: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise DhanApiError("Dhan API returned non-JSON response") from exc

    def get_orders(self) -> dict | list:
        return self._request("GET", self.ORDERS_PATH)

    def get_order(self, order_id: str) -> dict | list:
        return self._request("GET", f"{self.ORDERS_PATH}/{order_id}")

    def place_order(self, payload: dict) -> dict | list:
        return self._request("POST", self.ORDERS_PATH, json_body=payload)

    def cancel_order(self, order_id: str) -> dict | list:
        return self._request("DELETE", f"{self.ORDERS_PATH}/{order_id}")

    def get_positions(self) -> dict | list:
        return self._request("GET", self.POSITIONS_PATH)

    def get_holdings(self) -> dict | list:
        return self._request("GET", self.HOLDINGS_PATH)

    def get_funds(self) -> dict | list:
        return self._request("GET", self.FUNDS_PATH)
