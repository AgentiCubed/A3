"""Operator halt switch: a halted project dispatches nothing new.

Proves the next-steps Step-1 backend definition of done
(``docs/NEXT-STEPS-2026-07.md``): a halted project dispatches nothing new
while in-flight work concludes cleanly, halt/resume are audited and enforced
at every dispatch entry point (start, single-task dispatch, worker
advancement, inline chaining), and resume runs a work-conserving pass that
picks the chain back up.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.orchestration.ports import EngineStatus
from app.workers import tasks as worker_tasks
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"hl-{uuid.uuid4().hex[:10]}@example.com"
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


def _chain(client, headers) -> tuple[str, str, str]:
    """Seed a project with tasks A→B assigned to one mock AI agent."""
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    for t in (a, b):
        _assign(client, headers, pid, t, agent)
    _depend(client, headers, pid, a, b)
    return pid, a, b


def _statuses(client, headers, pid) -> dict[str, str]:
    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    return {t["id"]: t["status"] for t in tasks}


def _halt(client, headers, pid, body=None):
    return client.post(f"/api/v1/projects/{pid}/halt", json=body, headers=headers)


def _resume(client, headers, pid):
    return client.post(f"/api/v1/projects/{pid}/resume", json={}, headers=headers)


def _audits(project_id: str, action: str) -> list[dict]:
    async def _query():
        async with TestSessionFactory() as session:
            rows = (
                (
                    await session.execute(
                        select(AuditEvent).where(
                            AuditEvent.action == action,
                            AuditEvent.entity_id == uuid.UUID(project_id),
                        )
                    )
                )
                .scalars()
                .all()
            )
            return [r.after for r in rows]

    return asyncio.run(_query())


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


def test_halted_project_dispatches_nothing_new_while_inflight_concludes(client, monkeypatch):
    """The Step-1 acceptance test.

    Start dispatches A. The project is halted while A is in flight. The worker
    then finishes A cleanly — but its post-completion scheduling pass submits
    nothing, so B never dispatches while the halt stands.
    """
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    monkeypatch.setattr("app.workers.tasks.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid, a, b = _chain(client, headers)

    assert client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers).status_code == 200
    assert [call[0] for call in engine.calls] == [uuid.UUID(a)]

    resp = _halt(client, headers, pid, {"reason": "operator pause"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["halted_at"] is not None

    # In-flight A concludes cleanly through the real worker entrypoint...
    worker_tasks.set_session_factory(TestSessionFactory)
    try:
        worker_tasks.run_task_execution(a, engine.calls[0][1])
    finally:
        worker_tasks.set_session_factory(None)

    statuses = _statuses(client, headers, pid)
    assert statuses[a] == "completed"  # in-flight work finished, not aborted
    assert statuses[b] == "planned"  # nothing new dispatched
    assert len(engine.calls) == 1  # the worker's scheduling pass submitted nothing

    halted = _audits(pid, "project.halted")
    assert len(halted) == 1
    assert halted[0]["reason"] == "operator pause"


def test_start_and_dispatch_refused_while_halted(client, monkeypatch):
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid, a, _ = _chain(client, headers)
    assert _halt(client, headers, pid).status_code == 200

    resp = client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "project_halted"

    resp = client.post(f"/api/v1/projects/{pid}/tasks/{a}/dispatch", json={}, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "project_halted"

    assert engine.calls == []
    refusals = _audits(pid, "project.start_refused")
    assert any(r["reason"] == "project_halted" for r in refusals)


def test_resume_runs_work_conserving_pass_and_chain_completes(client, monkeypatch):
    """Predecessors that completed during the halt unlock on resume."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    monkeypatch.setattr("app.workers.tasks.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid, a, b = _chain(client, headers)

    client.post(f"/api/v1/projects/{pid}/start", json={}, headers=headers)
    _halt(client, headers, pid)
    worker_tasks.set_session_factory(TestSessionFactory)
    try:
        worker_tasks.run_task_execution(a, engine.calls[0][1])  # A finishes under halt
        assert len(engine.calls) == 1

        resp = _resume(client, headers, pid)
        assert resp.status_code == 200, resp.text
        assert [t["task_id"] for t in resp.json()["tasks"]] == [b]
        assert [call[0] for call in engine.calls] == [uuid.UUID(a), uuid.UUID(b)]

        worker_tasks.run_task_execution(b, engine.calls[1][1])
    finally:
        worker_tasks.set_session_factory(None)

    assert set(_statuses(client, headers, pid).values()) == {"completed"}
    assert len(_audits(pid, "project.resumed")) == 1


def test_halt_and_resume_reject_wrong_states(client):
    headers = _auth(client)
    pid = _project(client, headers)

    assert _resume(client, headers, pid).status_code == 409  # not halted
    assert _halt(client, headers, pid).status_code == 200
    assert _halt(client, headers, pid).status_code == 409  # already halted
    resp = _halt(client, headers, pid)
    assert resp.json()["detail"]["error"] == "already_halted"

    # A closed project can be neither halted nor resumed.
    pid2 = _project(client, headers)
    close = client.post(f"/api/v1/projects/{pid2}/close", json=None, headers=headers)
    assert close.status_code in (200, 409)
    closed_state = client.get(f"/api/v1/projects/{pid2}", headers=headers).json()["status"]
    if closed_state == "closed":
        assert _halt(client, headers, pid2).status_code == 409
        assert _halt(client, headers, pid2).json()["detail"]["error"] == "project_closed"


def test_halted_at_visible_on_project_reads(client):
    headers = _auth(client)
    pid = _project(client, headers)
    assert client.get(f"/api/v1/projects/{pid}", headers=headers).json()["halted_at"] is None
    _halt(client, headers, pid)
    assert client.get(f"/api/v1/projects/{pid}", headers=headers).json()["halted_at"] is not None
    _resume(client, headers, pid)
    assert client.get(f"/api/v1/projects/{pid}", headers=headers).json()["halted_at"] is None
