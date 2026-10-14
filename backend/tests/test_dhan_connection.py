import os
import tempfile

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from tradelens_ai.api import app
from tradelens_ai.services.assistant_search import requests_search, search_web
from tradelens_ai.services.broker_credentials_service import BrokerCredentialsService
from tradelens_ai.services.dhan_connection_service import (
    DhanConnectionError,
    DhanConnectionService,
)


class FakeDhanResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeDhanHTTP:
    requests = []

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def post(self, url, **kwargs):
        self.requests.append(("POST", url))
        assert url == "https://auth.dhan.co/app/generate-consent"
        assert kwargs["params"]["client_id"] == "customer-123"
        assert kwargs["headers"]["app_id"] == "app-id"
        return FakeDhanResponse({"consentAppId": "consent-example"})

    def get(self, url, **kwargs):
        self.requests.append(("GET", url))
        assert url == "https://auth.dhan.co/app/consumeApp-consent"
        assert kwargs["params"]["tokenId"] == "token-id-example"
        return FakeDhanResponse({
            "dhanClientId": "customer-123",
            "accessToken": "some-short-term-access-token",
            "expiryTime": "2026-10-15T15:00:00",
        })


@pytest.fixture
def connected_store(monkeypatch, tmp_path):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("TRADELENS_MASTER_KEY", key)
    credentials = BrokerCredentialsService(str(tmp_path / "broker.db"))
    credentials.update_profile(
        broker_name="dhan", client_id="customer-123",
        api_key="app-id", api_secret="app-secret", access_token=None,
    )
    return DhanConnectionService(str(tmp_path / "broker.db"), credentials), credentials


def test_dhan_approve_login_encrypts_token_once(monkeypatch, connected_store):
    connector, credentials = connected_store
    FakeDhanHTTP.requests = []
    monkeypatch.setattr(httpx, "Client", FakeDhanHTTP)
    start = connector.start()
    assert start["login_url"] == (
        "https://auth.dhan.co/login/consentApp-login?consentAppId=consent-example"
    )
    assert start["flow_state"]
    completed = connector.complete(start["flow_state"], "token-id-example")
    assert completed["connected"] is True
    assert "some-short-term-access-token" not in str(completed)
    assert credentials.reveal_secrets()["access_token"] == "some-short-term-access-token"
    with pytest.raises(DhanConnectionError, match="already used"):
        connector.complete(start["flow_state"], "token-id-example")
    assert FakeDhanHTTP.requests == [
        ("POST", "https://auth.dhan.co/app/generate-consent"),
        ("GET", "https://auth.dhan.co/app/consumeApp-consent"),
    ]


def test_dhan_invalid_state_never_exchanges_token(connected_store):
    connector, _ = connected_store
    with pytest.raises(DhanConnectionError, match="expired|already used"):
        connector.complete("a" * 40, "token-id-example")


def test_dhan_account_switch_never_inherits_broker_secrets(connected_store):
    connector, credentials = connected_store
    credentials.update_profile(
        broker_name="mock", client_id=None, api_key=None,
        api_secret=None, access_token=None,
    )
    values = credentials.reveal_secrets()
    assert values["broker_name"] == "mock"
    assert not values["api_key"]
    with pytest.raises(DhanConnectionError):
        connector.start()


def test_partial_credential_updates_preserve_existing_values(connected_store):
    _, credentials = connected_store
    credentials.update_profile(
        broker_name="dhan", client_id=None, api_key="new-key",
        access_token=None, api_secret=None,
    )
    data = credentials.reveal_secrets()
    assert data["client_id"] == "customer-123"
    assert data["api_key"] == "new-key"
    assert data["api_secret"] == "app-secret"


def test_search_without_provider_makes_no_false_claims(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    assert requests_search("Search web for NSE trading rules")
    result = search_web("Search web for NSE trading rules")
    assert result["configured"] is False
    assert result["results"] == []
    assert result["external_url"].startswith("https://search.brave.com/search?")


def test_broker_connect_requires_admin_token(monkeypatch):
    monkeypatch.delenv("TRADELENS_ADMIN_TOKEN", raising=False)
    response = TestClient(app).post("/broker/dhan/oauth/start")
    assert response.status_code == 503
