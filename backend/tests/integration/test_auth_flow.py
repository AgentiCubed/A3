"""End-to-end auth: register → login → me → refresh, plus failure paths."""

from __future__ import annotations

import uuid


def _email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


def _register(client, email: str, password: str = "supersecret123"):
    return client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": password},
    )


def test_register_login_me_refresh(client):
    email = _email()
    reg = _register(client, email)
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["email"] == email
    assert body["system_role"] == "owner"

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    assert login.status_code == 200, login.text
    tokens = login.json()
    access, refresh = tokens["access_token"], tokens["refresh_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == email

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]
    me2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me2.status_code == 200


def test_duplicate_email_conflicts(client):
    email = _email()
    assert _register(client, email).status_code == 201
    assert _register(client, email).status_code == 409


def test_login_wrong_password_401(client):
    email = _email()
    _register(client, email)
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "wrongwrong123"})
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_access_token_rejected_on_refresh_endpoint(client):
    email = _email()
    _register(client, email)
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    access = login.json()["access_token"]
    # Presenting an access token where a refresh token is required must fail.
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401
