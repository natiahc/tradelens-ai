import importlib
import tempfile

from fastapi.testclient import TestClient
import pytest

from tradelens_ai.services.assistant_service import (
    ChangeRequestStore, advisory_reply, contains_secret, guided_reply,
)

api_module = importlib.import_module("tradelens_ai.api.app")


def test_walkthrough_guides_new_user():
    text = guided_reply("How do I use this app?")
    assert "Small Capital Lab" in text
    assert "OHLC" in text
    assert "Audit" in text
    assert "guaranteed" in text


def test_without_ollama_or_openai_uses_guided(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TRADELENS_CHAT_PROVIDER", "auto")
    reply, mode = advisory_reply("How do I use this app?", [])
    assert mode == "guided"
    assert "Small Capital Lab" in reply


def test_request_never_saves_secrets(tmp_path):
    store = ChangeRequestStore(str(tmp_path / "changes.db"))
    item = store.save("Please add a new paper-trading RSI chart")
    assert item["status"] == "proposed"
    assert store.list_requests()[0]["request_id"] == item["request_id"]
    with pytest.raises(ValueError):
        store.save("api_key=supersecretkey123456789")


def test_secret_detection_and_chat_rejection(monkeypatch):
    monkeypatch.setenv("TRADELENS_CHAT_PROVIDER", "guided")
    assert contains_secret("access_token=secret-value-12345678")
    with pytest.raises(ValueError):
        advisory_reply("access_token=secret-value-12345678", [])


def test_ollama_fallback_without_reachable_server(monkeypatch):
    monkeypatch.setenv("TRADELENS_CHAT_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "invalid-url")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    result, mode = advisory_reply("How do I use this app?", [])
    assert mode == "guided"
    assert "Small Capital Lab" in result


def test_ollama_response_parsed_without_real_network(monkeypatch):
    import httpx

    recorded = {}

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, **kwargs):
            recorded["url"] = url
            recorded["payload"] = kwargs["json"]
            return httpx.Response(
                200, json={"message": {"role": "assistant", "content": "Open the Small Capital Lab."}},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setenv("TRADELENS_CHAT_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://ollama.example.org")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")
    monkeypatch.setattr(httpx, "Client", FakeClient)
    answer, mode = advisory_reply("Where should I start?", [])
    assert mode == "ollama"
    assert "Small Capital Lab" in answer
    assert recorded["url"] == "https://ollama.example.org/api/chat"
    assert recorded["payload"]["stream"] is False
    assert recorded["payload"]["messages"][0]["role"] == "system"


def test_assistant_endpoints_are_admin_only(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADELENS_ADMIN_TOKEN", "private-admin-test-key")
    monkeypatch.setenv("TRADELENS_CHAT_PROVIDER", "guided")
    api_module.assistant_request_store = ChangeRequestStore(str(tmp_path / "requests.db"))
    client = TestClient(api_module.app)

    unauthenticated = client.post("/assistant/chat", json={"message": "How do I use this app?"})
    assert unauthenticated.status_code == 401

    headers = {"X-TradeLens-Admin-Token": "private-admin-test-key"}
    response = client.post(
        "/assistant/chat", json={"message": "How do I use this app?"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "guided"
    assert response.json()["can_modify_repository"] is False
    assert response.json()["can_place_orders"] is False

    created = client.post("/assistant/requests", json={
        "description": "Add a mobile friendly portfolio risk tab"
    }, headers=headers)
    assert created.status_code == 200
    assert created.json()["status"] == "proposed"

    saved = client.get("/assistant/requests", headers=headers)
    assert saved.status_code == 200
    assert saved.json()[0]["request_id"] == created.json()["request_id"]
