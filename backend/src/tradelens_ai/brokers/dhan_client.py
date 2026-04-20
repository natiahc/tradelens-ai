from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DhanApiClient:
    client_id: str
    access_token: str
    base_url: str = "https://api.dhan.co"

    def auth_headers(self) -> dict[str, str]:
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
        }

    def build_url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        return f"{self.base_url}{path}"

    def get_orders(self) -> dict:
        raise NotImplementedError("HTTP integration for Dhan orders is not implemented yet")

    def place_order(self, payload: dict) -> dict:
        raise NotImplementedError("HTTP integration for Dhan place_order is not implemented yet")

    def cancel_order(self, order_id: str) -> dict:
        raise NotImplementedError("HTTP integration for Dhan cancel_order is not implemented yet")

    def get_positions(self) -> dict:
        raise NotImplementedError("HTTP integration for Dhan positions is not implemented yet")

    def get_holdings(self) -> dict:
        raise NotImplementedError("HTTP integration for Dhan holdings is not implemented yet")

    def get_funds(self) -> dict:
        raise NotImplementedError("HTTP integration for Dhan funds is not implemented yet")
