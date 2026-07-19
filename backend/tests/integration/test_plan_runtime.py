"""Approved-plan rubrics survive inline and Celery scheduling paths."""

from __future__ import annotations

from app.workers import tasks as worker_tasks
from tests.conftest import TestSessionFactory
from tests.integration.test_plan_approval import (
    _agent,
    _approval_payload,
    _approve,
    _auth,
    _draft,
    _project,
)
from tests.integration.test_scheduler import _CapturingEngine


def _approved_plan(client, headers) -> tuple[dict, dict]:
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    response = _approve(
        client,
        headers,
        project["id"],
        plan,
        _approval_payload(plan, executor),
    )
    assert response.status_code == 200, response.text
    return project, plan


def _tasks_by_key(client, headers, project_id: str) -> dict[str, dict]:
    tasks = client.get(f"/api/v1/projects/{project_id}/tasks", headers=headers).json()
    return {task["source_plan_task_key"]: task for task in tasks}


def _evaluation(client, headers, project_id: str, task_id: str) -> dict:
    rows = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert len(rows) == 1
    return rows[0]


def test_one_inline_start_evaluates_every_materialized_task(client):
    headers = _auth(client)
    project, _ = _approved_plan(client, headers)
    tasks = _tasks_by_key(client, headers, project["id"])

    response = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert response.status_code == 200, response.text
    assert {row["status"] for row in response.json()["tasks"]} == {"completed"}

    for task in tasks.values():
        evaluation = _evaluation(client, headers, project["id"], task["id"])
        assert evaluation["verdict"] == "pass"
        assert evaluation["rubric_source"] == "persisted"
        assert evaluation["rubric_specs"] == task["acceptance_criteria"]

    successor_execution = client.get(
        f"/api/v1/projects/{project['id']}/tasks/{tasks['deliver']['id']}/executions",
        headers=headers,
    ).json()[0]
    assert successor_execution["input_context"]["handoff"][0]["task_id"] == tasks["research"]["id"]
    assert successor_execution["input_context"]["evaluation"]["sources"] == ["persisted"]


def test_celery_initial_and_successor_workers_load_their_own_persisted_rubrics(client, monkeypatch):
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    monkeypatch.setattr("app.workers.tasks.get_workflow_engine", lambda: engine)

    headers = _auth(client)
    project, _ = _approved_plan(client, headers)
    tasks = _tasks_by_key(client, headers, project["id"])

    response = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert response.status_code == 200, response.text
    assert [str(call[0]) for call in engine.calls] == [tasks["research"]["id"]]
    assert "evaluation" not in engine.calls[0][1]

    worker_tasks.set_session_factory(TestSessionFactory)
    try:
        worker_tasks.run_task_execution(tasks["research"]["id"], engine.calls[0][1])
        assert [str(call[0]) for call in engine.calls] == [
            tasks["research"]["id"],
            tasks["deliver"]["id"],
        ]
        assert "evaluation" not in engine.calls[1][1]
        worker_tasks.run_task_execution(tasks["deliver"]["id"], engine.calls[1][1])
    finally:
        worker_tasks.set_session_factory(None)

    refreshed = _tasks_by_key(client, headers, project["id"])
    assert {task["status"] for task in refreshed.values()} == {"completed"}
    for task in refreshed.values():
        evaluation = _evaluation(client, headers, project["id"], task["id"])
        assert evaluation["verdict"] == "pass"
        assert evaluation["rubric_source"] == "persisted"
