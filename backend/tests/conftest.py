import pytest


@pytest.fixture(autouse=True)
def protected_test_api(monkeypatch):
    """Ensure operational API tests run with an isolated test-only admin secret."""
    monkeypatch.setenv("TRADELENS_ADMIN_TOKEN", "test-tradelens-token")
    monkeypatch.delenv("TRADELENS_ALLOW_LIVE_ORDERS", raising=False)
