"""Cross-tenant isolation and the USER_MANAGE guard."""

from __future__ import annotations

import uuid


def _register(client, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Org", "email": email, "password": "supersecret123"},
    )


def _login(client, email: str) -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    return r.json()["access_token"]


def test_members_list_is_org_scoped(client):
    a_email = f"a-{uuid.uuid4().hex[:8]}@example.com"
    b_email = f"b-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, a_email)
    b = _register(client, b_email)
    b_user_id = b.json()["id"]

    token_a = _login(client, a_email)
    resp = client.get("/api/v1/orgs/me/members", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    ids = {m["id"] for m in resp.json()}
    assert b_user_id not in ids  # owner A never sees org B's user


def test_cannot_modify_other_org_user(client):
    a_email = f"a-{uuid.uuid4().hex[:8]}@example.com"
    b_email = f"b-{uuid.uuid4().hex[:8]}@example.com"
    _register(client, a_email)
    b = _register(client, b_email)
    b_user_id = b.json()["id"]

    token_a = _login(client, a_email)
    resp = client.patch(
        f"/api/v1/orgs/me/members/{b_user_id}/role",
        json={"system_role": "admin"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    # Org-scoped repository returns None for a cross-org id → 404, never 200.
    assert resp.status_code == 404


def test_member_role_cannot_manage_users(client):
    """An owner can demote themselves to member; the member then loses USER_MANAGE."""
    email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    reg = _register(client, email)
    owner_id = reg.json()["id"]
    token = _login(client, email)

    # Owner demotes self to member (allowed: owner has USER_MANAGE).
    demote = client.patch(
        f"/api/v1/orgs/me/members/{owner_id}/role",
        json={"system_role": "member"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert demote.status_code == 200

    # Existing token still carries owner claims, but the guard re-checks the DB
    # user's role, so a fresh login reflecting 'member' is denied.
    member_token = _login(client, email)
    denied = client.patch(
        f"/api/v1/orgs/me/members/{owner_id}/role",
        json={"system_role": "owner"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert denied.status_code == 403
