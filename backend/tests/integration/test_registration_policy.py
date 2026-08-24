"""Registration gating, invite codes, auth rate limiting, credential-ref allowlist.

These are the hosted-deployment abuse controls: a public instance must be able
to close self-registration (or gate it behind an invite code), must throttle
credential guessing, and must never let user-supplied agent config read
arbitrary server env vars as an ``api_key_ref``.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.config import get_settings
from app.core.rate_limit import reset_auth_limiter


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def _register(client, email: str, invite_code: str | None = None):
    payload = {"organization_name": "Acme", "email": email, "password": "supersecret123"}
    if invite_code is not None:
        payload["invite_code"] = invite_code
    return client.post("/api/v1/auth/register", json=payload)


@pytest.fixture
def _settings_env(monkeypatch):
    """Apply env overrides to the cached Settings, restoring afterwards."""

    def apply(**env: str) -> None:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        get_settings.cache_clear()

    yield apply
    get_settings.cache_clear()


# ── Registration gate ─────────────────────────────────────────────────────


def test_registration_disabled_returns_403_before_email_probe(client, _settings_env):
    _settings_env(REGISTRATION_ENABLED="false")
    res = _register(client, _email())
    assert res.status_code == 403
    assert "closed" in res.json()["detail"]


def test_invite_code_required_when_configured(client, _settings_env):
    _settings_env(REGISTRATION_ENABLED="true", REGISTRATION_INVITE_CODE="sesame-open-123")
    # Missing and wrong codes are indistinguishable 403s.
    assert _register(client, _email()).status_code == 403
    assert _register(client, _email(), invite_code="wrong").status_code == 403
    # The right code registers normally.
    ok = _register(client, _email(), invite_code="sesame-open-123")
    assert ok.status_code == 201, ok.text


def test_registration_open_by_default(client):
    assert _register(client, _email()).status_code == 201


# ── Auth rate limiting ────────────────────────────────────────────────────


def test_login_rate_limit_returns_429_with_retry_after(client, _settings_env):
    _settings_env(AUTH_RATE_LIMIT_PER_MINUTE="3")
    reset_auth_limiter()  # rebuild with the tightened budget
    try:
        payload = {"email": _email(), "password": "wrong-password-123"}
        statuses = [client.post("/api/v1/auth/login", json=payload).status_code for _ in range(3)]
        assert statuses == [401, 401, 401]
        limited = client.post("/api/v1/auth/login", json=payload)
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) >= 1
    finally:
        reset_auth_limiter()


def test_register_rate_limit_scope_is_separate_from_login(client, _settings_env):
    _settings_env(AUTH_RATE_LIMIT_PER_MINUTE="2")
    reset_auth_limiter()
    try:
        # Exhaust the register scope...
        assert _register(client, _email()).status_code == 201
        assert _register(client, _email()).status_code == 201
        assert _register(client, _email()).status_code == 429
        # ...login still has its own budget.
        res = client.post(
            "/api/v1/auth/login",
            json={"email": _email(), "password": "supersecret123"},
        )
        assert res.status_code == 401  # wrong creds, but not rate limited
    finally:
        reset_auth_limiter()


# ── Credential-ref allowlist on agent config ──────────────────────────────


def _auth_headers(client) -> dict[str, str]:
    email = _email()
    assert _register(client, email).status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_agent_config_rejects_non_allowlisted_credential_ref(client):
    headers = _auth_headers(client)
    res = client.post(
        "/api/v1/agents",
        headers=headers,
        json={
            "name": "Exfiltrator",
            "kind": "ai",
            "provider": "gemini",
            "model": "gemini-flash-latest",
            "default_role": "executor",
            "config": {"api_key_ref": "SECRET_KEY"},
        },
    )
    assert res.status_code == 422
    assert "allowlisted" in res.json()["detail"]


def test_agent_config_accepts_allowlisted_credential_ref(client):
    headers = _auth_headers(client)
    res = client.post(
        "/api/v1/agents",
        headers=headers,
        json={
            "name": "Legit",
            "kind": "ai",
            "provider": "gemini",
            "model": "gemini-flash-latest",
            "default_role": "executor",
            "config": {"api_key_ref": "GEMINI_API_KEY"},
        },
    )
    assert res.status_code == 201, res.text
