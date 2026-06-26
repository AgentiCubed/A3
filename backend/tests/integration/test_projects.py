"""Planning domain: projects, methodology, tasks, dependencies, timeline,
Kanban, risks, cycle rejection, org scoping, and RBAC."""

from __future__ import annotations

import uuid


def _auth(client) -> dict[str, str]:
    email = f"pm-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _new_project(client, headers, **signals) -> str:
    body = {"name": "Launch", "objective": "ship it"}
    if signals:
        body["signals"] = signals
    resp = client.post("/api/v1/projects", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _new_task(client, headers, project_id, title, hours) -> str:
    resp = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": title, "estimate_hours": hours},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _dep(client, headers, project_id, pred, succ, **extra):
    return client.post(
        f"/api/v1/projects/{project_id}/dependencies",
        json={"predecessor_task_id": pred, "successor_task_id": succ, **extra},
        headers=headers,
    )


def test_create_project_recommends_methodology(client):
    headers = _auth(client)
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Flow", "objective": "x", "signals": {"continuous_flow": True}},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["methodology"]["methodology"] == "kanban"
    assert body["methodology"]["rationale"]


def test_full_planning_flow_and_critical_path(client):
    headers = _auth(client)
    pid = _new_project(client, headers, many_dependencies=True, hard_deadline=True)

    # Requirement + milestone.
    assert (
        client.post(
            f"/api/v1/projects/{pid}/requirements",
            json={"kind": "functional", "text": "must do X", "priority": "must"},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"/api/v1/projects/{pid}/milestones",
            json={"name": "Alpha"},
            headers=headers,
        ).status_code
        == 201
    )

    # Diamond: A(3)->B(2), A->C(4), B->D(2), C->D ; critical path A,C,D = 9h.
    a = _new_task(client, headers, pid, "A", 3)
    b = _new_task(client, headers, pid, "B", 2)
    c = _new_task(client, headers, pid, "C", 4)
    d = _new_task(client, headers, pid, "D", 2)
    for pred, succ in [(a, b), (a, c), (b, d), (c, d)]:
        assert _dep(client, headers, pid, pred, succ).status_code == 201

    timeline = client.get(f"/api/v1/projects/{pid}/timeline", headers=headers).json()
    assert timeline["project_duration"] == 9
    assert set(timeline["critical_path"]) == {a, c, d}
    assert b not in timeline["critical_path"]

    graph = client.get(f"/api/v1/projects/{pid}/graph", headers=headers).json()
    assert len(graph["nodes"]) == 4
    assert len(graph["edges"]) == 4
    critical_nodes = {n["id"] for n in graph["nodes"] if n["is_critical"]}
    assert critical_nodes == {a, c, d}


def test_dependency_cycle_rejected(client):
    headers = _auth(client)
    pid = _new_project(client, headers)
    a = _new_task(client, headers, pid, "A", 1)
    b = _new_task(client, headers, pid, "B", 1)
    assert _dep(client, headers, pid, a, b).status_code == 201
    cyclic = _dep(client, headers, pid, b, a)
    assert cyclic.status_code == 409
    assert cyclic.json()["detail"]["error"] == "dependency_cycle"


def test_self_and_duplicate_dependency_rejected(client):
    headers = _auth(client)
    pid = _new_project(client, headers)
    a = _new_task(client, headers, pid, "A", 1)
    b = _new_task(client, headers, pid, "B", 1)
    assert _dep(client, headers, pid, a, a).status_code == 409  # self-loop
    assert _dep(client, headers, pid, a, b).status_code == 201
    assert _dep(client, headers, pid, a, b).status_code == 409  # duplicate


def test_kanban_move(client):
    headers = _auth(client)
    pid = _new_project(client, headers)
    t = _new_task(client, headers, pid, "A", 1)
    resp = client.patch(
        f"/api/v1/projects/{pid}/tasks/{t}/kanban",
        json={"kanban_column": "in_progress"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["kanban_column"] == "in_progress"


def test_risk_severity_computed(client):
    headers = _auth(client)
    pid = _new_project(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/risks",
        json={"title": "vendor slip", "likelihood": 4, "impact": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["severity"] == 20


def test_project_is_org_scoped(client):
    headers_a = _auth(client)
    pid = _new_project(client, headers_a)
    headers_b = _auth(client)  # different org
    assert client.get(f"/api/v1/projects/{pid}", headers=headers_b).status_code == 404


def test_member_cannot_create_project(client):
    """Demote the owner to member, then project creation is forbidden."""
    email = f"demote-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    uid = reg.json()["id"]
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.patch(
        f"/api/v1/orgs/me/members/{uid}/role", json={"system_role": "member"}, headers=headers
    )
    member_token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    resp = client.post(
        "/api/v1/projects",
        json={"name": "X", "objective": "y"},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403
