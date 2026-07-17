"""WS-2 dependency-aware scheduler: a single start call runs a task chain.

Proves the remediation-plan WS-2 definition of done, hermetically: a seeded
three-task chain A→B→C completes end-to-end from one ``POST /projects/{id}/start``
call with no per-task API calls (inline mode), and in celery mode the worker
advances the chain one dependency level at a time.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.orchestration.ports import EngineStatus
from app.workers import tasks as worker_tasks
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"sc-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _project(client, headers) -> str:
    return client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]


def _task(client, headers, pid, title) -> str:
    return client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": title}, headers=headers
    ).json()["id"]


def _agent(client, headers, name="Worker") -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]


def _assign(client, headers, pid, task_id, agent_id) -> None:
    resp = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


def _depend(client, headers, pid, predecessor, successor) -> None:
    resp = client.post(
        f"/api/v1/projects/{pid}/dependencies",
        json={"predecessor_task_id": predecessor, "successor_task_id": successor},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


def _chain(client, headers) -> tuple[str, str, str, str]:
    """Seed a project with tasks A→B→C all assigned to one mock AI agent."""
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    c = _task(client, headers, pid, "C")
    agent = _agent(client, headers)
    for t in (a, b, c):
        _assign(client, headers, pid, t, agent)
    _depend(client, headers, pid, a, b)
    _depend(client, headers, pid, b, c)
    return pid, a, b, c


def _statuses(client, headers, pid) -> dict[str, str]:
    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    return {t["id"]: t["status"] for t in tasks}


class _CapturingEngine:
    """WorkflowEngine double: records submissions instead of queueing them."""

    name = "celery"

    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, dict[str, Any] | None]] = []

    def submit_execution(self, work_id: uuid.UUID, params: dict[str, Any] | None = None) -> str:
        self.calls.append((work_id, params))
        return f"handle-{len(self.calls)}"

    def signal_cancel(self, handle: str) -> None:  # pragma: no cover - unused
        raise NotImplementedError

    def get_status(self, handle: str) -> EngineStatus:  # pragma: no cover - unused
        raise NotImplementedError


def test_inline_start_completes_full_chain_in_one_call(client):
    """The WS-2 acceptance test: A→B→C from a single start call, in order."""
    headers = _auth(client)
    pid, a, b, c = _chain(client, headers)

    resp = client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["engine"] == "inline"
    assert {t["task_id"] for t in body["tasks"]} == {a, b, c}
    assert all(t["status"] == "completed" for t in body["tasks"])

    assert set(_statuses(client, headers, pid).values()) == {"completed"}

    # Dependency order was respected: each task finished before its successor started.
    def _span(task_id: str) -> tuple[datetime, datetime]:
        execs = client.get(
            f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers
        ).json()
        assert len(execs) == 1
        return (
            datetime.fromisoformat(execs[0]["started_at"]),
            datetime.fromisoformat(execs[0]["finished_at"]),
        )

    a_start, a_finish = _span(a)
    b_start, b_finish = _span(b)
    c_start, _ = _span(c)
    assert a_start <= a_finish <= b_start <= b_finish <= c_start


def test_celery_start_queues_only_dependency_satisfied_wave(client, monkeypatch):
    """Start dispatches A only; B and C wait for their predecessors."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid, a, b, c = _chain(client, headers)

    resp = client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["engine"] == "celery"
    assert [t["task_id"] for t in body["tasks"]] == [a]
    assert body["tasks"][0]["status"] == "queued"

    statuses = _statuses(client, headers, pid)
    assert statuses[a] == "queued"
    assert statuses[b] == "planned"
    assert statuses[c] == "planned"
    assert [call[0] for call in engine.calls] == [uuid.UUID(a)]


def test_worker_completion_advances_chain_to_the_end(client, monkeypatch):
    """Each worker completion dispatches the newly-unblocked successor."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    monkeypatch.setattr("app.workers.tasks.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid, a, b, c = _chain(client, headers)

    assert client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers).status_code == 200
    assert [call[0] for call in engine.calls] == [uuid.UUID(a)]

    worker_tasks.set_session_factory(TestSessionFactory)
    try:
        # Worker finishes A → scheduler submits B with system-actor params.
        worker_tasks.run_task_execution(a, engine.calls[0][1])
        statuses = _statuses(client, headers, pid)
        assert statuses[a] == "completed"
        assert statuses[b] == "queued"
        assert statuses[c] == "planned"
        assert [call[0] for call in engine.calls] == [uuid.UUID(a), uuid.UUID(b)]
        assert engine.calls[1][1]["actor_type"] == "system"

        # B → C, then C → nothing left to dispatch.
        worker_tasks.run_task_execution(b, engine.calls[1][1])
        assert [call[0] for call in engine.calls] == [uuid.UUID(a), uuid.UUID(b), uuid.UUID(c)]
        worker_tasks.run_task_execution(c, engine.calls[2][1])
        assert len(engine.calls) == 3
    finally:
        worker_tasks.set_session_factory(None)

    assert set(_statuses(client, headers, pid).values()) == {"completed"}


def test_start_respects_concurrency_cap(client, monkeypatch):
    """Independent tasks are dispatched only up to SCHEDULER_MAX_PARALLEL."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    monkeypatch.setattr(get_settings(), "scheduler_max_parallel", 2)

    headers = _auth(client)
    pid = _project(client, headers)
    agent = _agent(client, headers)
    task_ids = [_task(client, headers, pid, f"T{i}") for i in range(4)]
    for t in task_ids:
        _assign(client, headers, pid, t, agent)

    resp = client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["tasks"]) == 2
    assert len(engine.calls) == 2
    statuses = _statuses(client, headers, pid)
    assert sorted(statuses.values()) == ["planned", "planned", "queued", "queued"]


def test_unassigned_predecessor_gates_successor(client, monkeypatch):
    """An unschedulable predecessor keeps its successors out of dispatch."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")  # never assigned: not schedulable
    b = _task(client, headers, pid, "B")
    _assign(client, headers, pid, b, _agent(client, headers))
    _depend(client, headers, pid, a, b)

    resp = client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tasks"] == []
    assert engine.calls == []
    statuses = _statuses(client, headers, pid)
    assert statuses[a] == "planned"
    assert statuses[b] == "planned"
