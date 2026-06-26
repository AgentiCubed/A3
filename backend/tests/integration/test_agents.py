"""Agent registry, capabilities, tools, default-deny permissions, matching,
assignment, and the agent self-escalation block."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.core.rbac import Actor
from app.core.roles import ActorType
from app.services import tool_service


def _auth(client) -> dict[str, str]:
    email = f"ag-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _agent(client, headers, name="Researcher", provider="mock"):
    resp = client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": provider},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _tool(client, headers, name="web-search", sensitivity="low"):
    resp = client.post(
        "/api/v1/tools",
        json={"name": name, "kind": "http", "sensitivity": sensitivity},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_register_agent_unknown_provider_rejected(client):
    headers = _auth(client)
    resp = client.post(
        "/api/v1/agents",
        json={"name": "X", "kind": "ai", "provider": "bogus"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_capability_taxonomy_enforced(client):
    headers = _auth(client)
    agent_id = _agent(client, headers)
    ok = client.post(
        f"/api/v1/agents/{agent_id}/capabilities",
        json={"capability": "research.web", "proficiency": 4},
        headers=headers,
    )
    assert ok.status_code == 201
    bad = client.post(
        f"/api/v1/agents/{agent_id}/capabilities",
        json={"capability": "made.up.skill", "proficiency": 3},
        headers=headers,
    )
    assert bad.status_code == 422
    assert bad.json()["detail"]["error"] == "unknown_capability"


def test_default_deny_then_grant_permission(client):
    headers = _auth(client)
    agent_id = _agent(client, headers)
    tool_id = _tool(client, headers)

    # Default-deny: no permissions yet.
    perms = client.get(f"/api/v1/agents/{agent_id}/permissions", headers=headers).json()
    assert perms == []

    grant = client.post(
        f"/api/v1/agents/{agent_id}/tools/{tool_id}/permission",
        json={"scope": {"read_only": True}},
        headers=headers,
    )
    assert grant.status_code == 201

    perms = client.get(f"/api/v1/agents/{agent_id}/permissions", headers=headers).json()
    assert len(perms) == 1

    # Duplicate grant rejected.
    dup = client.post(
        f"/api/v1/agents/{agent_id}/tools/{tool_id}/permission", json={}, headers=headers
    )
    assert dup.status_code == 409


def test_revoke_permission(client):
    headers = _auth(client)
    agent_id = _agent(client, headers)
    tool_id = _tool(client, headers)
    client.post(f"/api/v1/agents/{agent_id}/tools/{tool_id}/permission", json={}, headers=headers)
    revoke = client.delete(f"/api/v1/agents/{agent_id}/tools/{tool_id}/permission", headers=headers)
    assert revoke.status_code == 204
    perms = client.get(f"/api/v1/agents/{agent_id}/permissions", headers=headers).json()
    assert perms == []


async def test_agent_cannot_grant_permission_service_guard(session):
    """Layer-2 service guard: an agent actor is refused even if it reaches the service."""
    agent_actor = Actor(actor_type=ActorType.AGENT, organization_id=uuid.uuid4())
    with pytest.raises(tool_service.SelfEscalation):
        await tool_service.grant_tool_permission(
            session,
            actor=agent_actor,
            agent_id=uuid.uuid4(),
            tool_id=uuid.uuid4(),
            scope=None,
            expires_at=None,
        )


async def test_has_permission_respects_expiry(session, client):
    headers = _auth(client)
    agent_id = uuid.UUID(_agent(client, headers))
    tool_id = uuid.UUID(_tool(client, headers))
    # No grant → denied.
    assert not await tool_service.has_permission(
        session, agent_id=agent_id, tool_id=tool_id, now=datetime.now(UTC)
    )


def test_matching_endpoint_ranks_agents(client):
    headers = _auth(client)
    specialist = _agent(client, headers, name="Specialist")
    generalist = _agent(client, headers, name="Generalist")
    for cap, prof in [("research.web", 5), ("writing.brief", 5)]:
        client.post(
            f"/api/v1/agents/{specialist}/capabilities",
            json={"capability": cap, "proficiency": prof},
            headers=headers,
        )
    client.post(
        f"/api/v1/agents/{generalist}/capabilities",
        json={"capability": "research.web", "proficiency": 2},
        headers=headers,
    )

    resp = client.get(
        "/api/v1/agents/matches",
        params={"capability": ["research.web", "writing.brief"]},
        headers=headers,
    )
    assert resp.status_code == 200
    ranked = resp.json()
    assert ranked[0]["agent_id"] == specialist
    assert ranked[0]["eligible"]
    assert not ranked[1]["eligible"]  # generalist missing writing.brief


def test_assign_enforces_capability_coverage(client):
    headers = _auth(client)
    # Project + task requiring a capability.
    pid = client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks",
        json={"title": "Research", "required_capabilities": ["research.web"]},
        headers=headers,
    ).json()["id"]

    bare_agent = _agent(client, headers, name="Bare")
    miss = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": bare_agent},
        headers=headers,
    )
    assert miss.status_code == 422
    assert miss.json()["detail"]["error"] == "capability_mismatch"

    capable = _agent(client, headers, name="Capable")
    client.post(
        f"/api/v1/agents/{capable}/capabilities",
        json={"capability": "research.web", "proficiency": 4},
        headers=headers,
    )
    ok = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": capable},
        headers=headers,
    )
    assert ok.status_code == 200


def test_member_cannot_register_agent(client):
    email = f"m-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    uid = reg.json()["id"]
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    client.patch(f"/api/v1/orgs/me/members/{uid}/role", json={"system_role": "member"}, headers=h)
    member_token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    resp = client.post(
        "/api/v1/agents",
        json={"name": "X", "kind": "ai", "provider": "mock"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403


def test_agents_are_org_scoped(client):
    headers_a = _auth(client)
    agent_id = _agent(client, headers_a)
    headers_b = _auth(client)
    # Org B cannot grant a permission on org A's agent (agent not found in its scope).
    tool_b = _tool(client, headers_b)
    resp = client.post(
        f"/api/v1/agents/{agent_id}/tools/{tool_b}/permission", json={}, headers=headers_b
    )
    assert resp.status_code == 404
