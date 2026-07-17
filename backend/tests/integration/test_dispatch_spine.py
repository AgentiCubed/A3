"""WS-1 execution spine: async dispatch through the WorkflowEngine port.

Proves the remediation-plan WS-1 definition of done, hermetically:
dispatch returns before execution happens, the queued task carries the
caller's exact parameters, and the worker path later runs it with them.
The real-broker variant lives in test_celery_broker_smoke.py.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.roles import ActorType
from app.orchestration.ports import EngineStatus
from app.services import execution_service
from app.workers import tasks as worker_tasks
from app.workers.tasks import _parse_dispatch_params
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"sp-{uuid.uuid4().hex[:10]}@example.com"
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


def _task(client, headers, pid, title="Do work") -> str:
    return client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": title}, headers=headers
    ).json()["id"]


def _agent(client, headers, name="Worker") -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]


def _assign(client, headers, pid, task_id, agent_id):
    return client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )


class _CapturingEngine:
    """WorkflowEngine double: records submissions instead of queueing them."""

    name = "celery"

    def __init__(self) -> None:
        self.calls: list[tuple[uuid.UUID, dict[str, Any] | None]] = []

    def submit_execution(self, work_id: uuid.UUID, params: dict[str, Any] | None = None) -> str:
        self.calls.append((work_id, params))
        return "handle-test"

    def signal_cancel(self, handle: str) -> None:  # pragma: no cover - unused
        raise NotImplementedError

    def get_status(self, handle: str) -> EngineStatus:  # pragma: no cover - unused
        raise NotImplementedError


def test_async_dispatch_returns_before_execution_then_worker_runs_it(client, monkeypatch):
    """The WS-1 acceptance test.

    1. In celery mode, dispatch returns DispatchAccepted with the task QUEUED
       and zero execution rows — the request did not execute anything.
    2. The worker entrypoint, invoked with the exact captured params, then
       completes the task (including the idempotent re-entry through QUEUED).
    """
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    agent_id = _agent(client, headers)
    assert _assign(client, headers, pid, task_id, agent_id).status_code == 200

    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"max_attempts": 1, "timeout_s": 5.0},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "queued"
    assert body["engine"] == "celery"
    assert body["engine_handle"] == "handle-test"
    assert body["task_id"] == task_id

    # Returned before execution: task QUEUED, no execution rows yet.
    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "queued"
    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert execs == []

    # The engine received exactly one submission: the task id + caller params.
    assert len(engine.calls) == 1
    work_id, params = engine.calls[0]
    assert work_id == uuid.UUID(task_id)
    assert params["max_attempts"] == 1
    assert params["timeout_s"] == 5.0
    assert params["actor_type"] == "user"
    assert params["actor_id"] is not None

    # Worker path runs with exactly those params and completes the task.
    worker_tasks.set_session_factory(TestSessionFactory)
    try:
        worker_tasks.run_task_execution(task_id, params)
    finally:
        worker_tasks.set_session_factory(None)

    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "completed"
    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert len(execs) == 1 and execs[0]["state"] == "completed"


def test_async_dispatch_rejects_unassigned_without_queueing(client, monkeypatch):
    """Dispatchability is validated at the API; the worker never sees junk."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)  # no agent assigned

    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.status_code == 422
    assert engine.calls == []


def test_dispatch_rejects_evaluator_equal_to_executor(client, monkeypatch):
    """Executor/evaluator separation is enforced before queueing (ADR-0004)."""
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    agent_id = _agent(client, headers)
    _assign(client, headers, pid, task_id, agent_id)

    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"evaluator_agent_id": agent_id},
        headers=headers,
    )
    assert resp.status_code == 422
    assert engine.calls == []


class _FailingEngine:
    """WorkflowEngine double whose broker is unreachable."""

    name = "celery"

    def submit_execution(self, work_id: uuid.UUID, params: dict[str, Any] | None = None) -> str:
        raise ConnectionError("broker down")

    def signal_cancel(self, handle: str) -> None:  # pragma: no cover - unused
        raise NotImplementedError

    def get_status(self, handle: str) -> EngineStatus:  # pragma: no cover - unused
        raise NotImplementedError


def test_submit_failure_parks_task_blocked_then_redispatchable(client, monkeypatch):
    """Broker failure after the QUEUED commit must not strand the task.

    The endpoint parks it in BLOCKED (audited, re-dispatchable) and returns
    503; once the engine is healthy again, dispatch succeeds from BLOCKED.
    """
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: _FailingEngine())

    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    agent_id = _agent(client, headers)
    _assign(client, headers, pid, task_id, agent_id)

    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.status_code == 503

    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "blocked"
    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert execs == []

    # Broker recovers: the BLOCKED task dispatches cleanly.
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"
    assert len(engine.calls) == 1


def test_dispatch_params_round_trip():
    """build_dispatch_params and the worker's parser cannot drift apart."""
    actor = uuid.uuid4()
    evaluator = uuid.uuid4()
    params = execution_service.build_dispatch_params(
        actor_id=actor,
        actor_type=ActorType.USER,
        max_attempts=3,
        timeout_s=12.5,
        evaluation=execution_service.EvaluationConfig(
            rubric_specs=[{"kind": "contains", "value": "x"}],
            evaluator_agent_id=evaluator,
            max_remediations=2,
        ),
    )
    kwargs = _parse_dispatch_params(params)
    assert kwargs["actor_id"] == actor
    assert kwargs["actor_type"] == ActorType.USER
    assert kwargs["max_attempts"] == 3
    assert kwargs["timeout_s"] == 12.5
    cfg = kwargs["evaluation"]
    assert cfg.rubric_specs == [{"kind": "contains", "value": "x"}]
    assert cfg.evaluator_agent_id == evaluator
    assert cfg.max_remediations == 2


def test_dispatch_params_round_trip_minimal():
    params = execution_service.build_dispatch_params(
        actor_id=None, actor_type=ActorType.SYSTEM, max_attempts=2, timeout_s=30.0, evaluation=None
    )
    kwargs = _parse_dispatch_params(params)
    assert kwargs["actor_id"] is None
    assert kwargs["actor_type"] == ActorType.SYSTEM
    assert "evaluation" not in kwargs
