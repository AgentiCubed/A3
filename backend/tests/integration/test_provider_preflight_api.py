"""HTTP surface for provider listing and preflight."""

from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.core.rate_limit import reset_auth_limiter, reset_preflight_limiter
from app.orchestration.ports import ProviderErrorCategory


def _auth(client) -> dict[str, str]:
    email = f"preflight-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "supersecret123",
            "organization_name": "Preflight Org",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "supersecret123"},
    ).json()["access_token"]
    return {"Authorization": "Bearer " + token}


def test_list_providers_requires_auth(client):
    assert client.get("/api/v1/providers").status_code == 401


def test_list_providers_returns_selectable_names(client):
    headers = _auth(client)
    response = client.get("/api/v1/providers", headers=headers)
    assert response.status_code == 200
    providers = response.json()["providers"]
    assert "mock" in providers
    assert "gemini" in providers
    assert "github_models" not in providers  # retired, not selectable


def test_preflight_mock_passes(client):
    headers = _auth(client)
    response = client.post(
        "/api/v1/providers/preflight",
        json={"provider": "mock"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["provider"] == "mock"
    assert body["diagnostic"] is None


def test_preflight_missing_credential_is_actionable(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    headers = _auth(client)
    response = client.post(
        "/api/v1/providers/preflight",
        json={"provider": "gemini"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["category"] == "authentication"
    assert "Credential missing or malformed" in body["message"]
    assert body["diagnostic"] == (
        "provider_http_status=none provider_error_category=authentication"
    )


def test_preflight_retired_provider_names_replacement(client):
    headers = _auth(client)
    response = client.post(
        "/api/v1/providers/preflight",
        json={"provider": "github_models"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["http_status"] == 410
    assert "gemini" in body["message"]


def test_preflight_never_echoes_exception_text(client, monkeypatch):
    class _Leaky:
        name = "gemini"

        async def run(self, _request):
            raise RuntimeError("secret=super-secret-token host=internal.example")

    monkeypatch.setattr(
        "app.services.provider_preflight.get_adapter",
        lambda _name: _Leaky(),
    )
    headers = _auth(client)
    response = client.post(
        "/api/v1/providers/preflight",
        json={"provider": "gemini"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    blob = str(body)
    assert "super-secret-token" not in blob
    assert "internal.example" not in blob
    assert body["category"] == ProviderErrorCategory.PROVIDER_UNAVAILABLE.value


def test_preflight_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()
    reset_auth_limiter()
    reset_preflight_limiter()
    try:
        headers = _auth(client)
        first = client.post(
            "/api/v1/providers/preflight",
            json={"provider": "mock"},
            headers=headers,
        )
        assert first.status_code == 200
        limited = client.post(
            "/api/v1/providers/preflight",
            json={"provider": "mock"},
            headers=headers,
        )
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) >= 1
    finally:
        reset_auth_limiter()
        reset_preflight_limiter()
        get_settings.cache_clear()
