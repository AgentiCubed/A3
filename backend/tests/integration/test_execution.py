"""Task dispatch: success, retry+escalation, timeout, reassignment, history,
immutable executions, and the worker engine running an execution end-to-end."""

from __future__ import annotations

import uuid

import pytest

from app.db.base import ImmutableError
from app.models.task_execution import TaskExecution
from app.orchestration.ports import ProviderCallError, ProviderErrorCategory
from app.services import execution_service


def _auth(client) -> dict[str, str]:
    email = f"ex-{uuid.uuid4().hex[:10]}@example.com"
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


def _agent(client, headers, name="Worker", provider="mock") -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": provider},
        headers=headers,
    ).json()["id"]


def _assign(client, headers, pid, task_id, agent_id):
    return client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )


def test_dispatch_success(client):
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    agent_id = _agent(client, headers)
    assert _assign(client, headers, pid, task_id, agent_id).status_code == 200

    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["final_state"] == "completed"
    assert body["attempts"] == 1
    assert not body["escalated"]
    assert body["output"]

    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert len(execs) == 1
    assert execs[0]["state"] == "completed"


def test_dispatch_retries_then_escalates(client):
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid, title="Crash [[FAIL]]")
    agent_id = _agent(client, headers)
    _assign(client, headers, pid, task_id, agent_id)

    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"max_attempts": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_state"] == "blocked"
    assert body["attempts"] == 2
    assert body["escalated"]

    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert len(execs) == 2
    assert all(e["state"] == "failed" for e in execs)

    # The task is now BLOCKED (escalated to a human).
    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "blocked"


def test_provider_failure_persists_only_safe_diagnostic(client, monkeypatch):
    class _FailingProvider:
        async def run(self, _request):
            raise ProviderCallError(
                http_status=403,
                category=ProviderErrorCategory.AUTHORIZATION,
            )

    monkeypatch.setattr(execution_service, "get_adapter", lambda _name: _FailingProvider())
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    agent_id = _agent(client, headers, provider="github_models")
    _assign(client, headers, pid, task_id, agent_id)

    response = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"max_attempts": 1},
        headers=headers,
    )
    assert response.status_code == 200
    executions = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers
    ).json()
    err = executions[0]["error"]
    assert "provider_http_status=403" in err
    assert "provider_error_category=authorization" in err
    assert "Provider refused access" in err


def test_dispatch_timeout_escalates(client):
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid, title="Slow [[SLEEP:0.3]]")
    agent_id = _agent(client, headers)
    _assign(client, headers, pid, task_id, agent_id)

    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"max_attempts": 1, "timeout_s": 0.05},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_state"] == "blocked"
    assert body["escalated"]
    execs = client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()
    assert "timeout" in execs[0]["error"]


def test_reassign_then_redispatch_completes(client):
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid, title="Flaky [[FAIL]]")
    bad = _agent(client, headers, name="Bad")
    _assign(client, headers, pid, task_id, bad)
    client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"max_attempts": 1},
        headers=headers,
    )

    # Reassign to a fresh agent and fix the task so it no longer fails.
    good = _agent(client, headers, name="Good")
    reassign = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/reassign",
        json={"agent_id": good},
        headers=headers,
    )
    assert reassign.status_code == 200
    assert reassign.json()["status"] == "ready"


def test_dispatch_unassigned_task_422(client):
    headers = _auth(client)
    pid = _project(client, headers)
    task_id = _task(client, headers, pid)
    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.status_code == 422


async def test_task_execution_is_immutable(session):
    execution = TaskExecution(
        organization_id=uuid.uuid4(),
        task_id=uuid.uuid4(),
        attempt_number=1,
        state="completed",
        output="x",
    )
    session.add(execution)
    await session.commit()
    execution.output = "tampered"
    with pytest.raises(ImmutableError):
        await session.commit()


def test_worker_runs_execution_via_engine_port(client):
    """CeleryWorkflowEngine (eager) runs execute_task end-to-end through the port."""
    from app.orchestration.engines import CeleryWorkflowEngine
    from app.workers import tasks as worker_tasks
    from app.workers.celery_app import celery_app
    from tests.conftest import TestSessionFactory

    worker_tasks.set_session_factory(TestSessionFactory)
    celery_app.conf.task_always_eager = True
    try:
        headers = _auth(client)
        pid = _project(client, headers)
        task_id = _task(client, headers, pid)
        agent_id = _agent(client, headers)
        _assign(client, headers, pid, task_id, agent_id)

        engine = CeleryWorkflowEngine()
        handle = engine.submit_execution(uuid.UUID(task_id))
        assert handle  # a celery task id

        tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
        assert next(t for t in tasks if t["id"] == task_id)["status"] == "completed"
        execs = client.get(
            f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers
        ).json()
        assert len(execs) == 1 and execs[0]["state"] == "completed"
    finally:
        worker_tasks.set_session_factory(None)
