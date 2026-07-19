"""Persisted task rubrics are authoritative across every execution entry point."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.enums import AgentStatus
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationCriterion
from app.models.task import Task
from app.models.task_execution import TaskExecution
from tests.conftest import TestSessionFactory

_PASS = {"key": "quality", "check": "non_empty"}
_FAIL = {
    "key": "governed_token",
    "check": "contains_all",
    "params": {"keywords": ["ABSENT_GOVERNED_TOKEN"]},
}


def _auth(client) -> dict[str, str]:
    email = f"rubric-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup(client, headers) -> tuple[str, str, str]:
    project_id = client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Governed work"},
        headers=headers,
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": "Executor", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    assigned = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    assert assigned.status_code == 200, assigned.text
    return project_id, task_id, agent_id


def _agent(client, headers, name: str) -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": "mock", "default_role": "either"},
        headers=headers,
    ).json()["id"]


def _set_policy(
    task_id: str,
    criteria: object,
    *,
    evaluator_agent_id: str | None = None,
    max_remediations: int = 1,
) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            assert task is not None
            task.acceptance_criteria = criteria
            task.evaluator_agent_id = (
                uuid.UUID(evaluator_agent_id) if evaluator_agent_id is not None else None
            )
            task.max_remediations = max_remediations
            await session.commit()

    asyncio.run(_update())


def _disable_agent(agent_id: str) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            agent = await session.get(Agent, uuid.UUID(agent_id))
            assert agent is not None
            agent.status = AgentStatus.DISABLED
            await session.commit()

    asyncio.run(_update())


def _criterion_count(task_id: str) -> int:
    async def _query():
        async with TestSessionFactory() as session:
            return await session.scalar(
                select(func.count(EvaluationCriterion.id))
                .join(Evaluation, EvaluationCriterion.evaluation_id == Evaluation.id)
                .join(TaskExecution, Evaluation.task_execution_id == TaskExecution.id)
                .where(TaskExecution.task_id == uuid.UUID(task_id))
            )

    return int(asyncio.run(_query()) or 0)


def test_legacy_manual_task_without_policy_remains_ungraded(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch", json={}, headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["final_state"] == "completed"
    evaluations = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert evaluations == []


def test_persisted_rubric_is_used_and_provenanced_without_request_overlay(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    _set_policy(task_id, [_PASS])

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch", json={}, headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["verdict"] == "pass"

    evaluations = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert len(evaluations) == 1
    assert evaluations[0]["rubric_specs"] == [
        {"check": "non_empty", "key": "quality", "params": {}, "weight": 1.0}
    ]
    assert len(evaluations[0]["rubric_sha256"]) == 64
    assert evaluations[0]["rubric_source"] == "persisted"
    execution = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
    ).json()[0]
    assert (
        execution["input_context"]["evaluation"]["rubric_sha256"] == evaluations[0]["rubric_sha256"]
    )
    assert execution["input_context"]["evaluation"]["sources"] == ["persisted"]


def test_request_rubric_is_additive_and_cannot_replace_failing_persisted_gate(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    _set_policy(task_id, [_FAIL], max_remediations=0)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch",
        json={"rubric": [{"key": "request_nonempty", "check": "non_empty"}]},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["final_state"] == "awaiting_approval"
    assert response.json()["verdict"] in {"fail", "needs_revision"}
    evaluations = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert evaluations[0]["rubric_source"] == "persisted+request"
    assert [spec["key"] for spec in evaluations[0]["rubric_specs"]] == [
        "governed_token",
        "request_nonempty",
    ]
    assert _criterion_count(task_id) == 2


def test_exact_duplicate_overlay_is_deduplicated(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    _set_policy(task_id, [_PASS])

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch",
        json={"rubric": [_PASS]},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert _criterion_count(task_id) == 1
    evaluation = client.get(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/evaluations", headers=headers
    ).json()[0]
    assert len(evaluation["rubric_specs"]) == 1


def test_conflicting_overlay_or_evaluator_fails_before_provider_execution(client):
    headers = _auth(client)
    project_id, task_id, executor = _setup(client, headers)
    _set_policy(task_id, [_PASS])
    conflict = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch",
        json={
            "rubric": [
                {
                    "key": "quality",
                    "check": "contains_all",
                    "params": {"keywords": ["different"]},
                }
            ]
        },
        headers=headers,
    )
    assert conflict.status_code == 422
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
        ).json()
        == []
    )

    governed_evaluator = _agent(client, headers, "Governed evaluator")
    requested_evaluator = _agent(client, headers, "Requested evaluator")
    _set_policy(task_id, [_PASS], evaluator_agent_id=governed_evaluator)
    override = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch",
        json={"evaluator_agent_id": requested_evaluator},
        headers=headers,
    )
    assert override.status_code == 422
    assert governed_evaluator != requested_evaluator != executor
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
        ).json()
        == []
    )


def test_malformed_persisted_rubric_fails_closed_before_provider_execution(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    _set_policy(task_id, {"criteria": [_PASS]})

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch", json={}, headers=headers
    )
    assert response.status_code == 422
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
        ).json()
        == []
    )


def test_executor_eligibility_is_rechecked_at_dispatch(client):
    headers = _auth(client)
    project_id, task_id, executor = _setup(client, headers)
    _disable_agent(executor)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch", json={}, headers=headers
    )
    assert response.status_code == 422
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
        ).json()
        == []
    )


def test_governed_evaluator_capability_is_rechecked_at_dispatch(client):
    headers = _auth(client)
    project_id, task_id, _ = _setup(client, headers)
    evaluator = _agent(client, headers, "Evaluator without rubric capability")
    _set_policy(task_id, [_PASS], evaluator_agent_id=evaluator)

    response = client.post(
        f"/api/v1/projects/{project_id}/tasks/{task_id}/dispatch", json={}, headers=headers
    )
    assert response.status_code == 422
    assert (
        client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}/executions", headers=headers
        ).json()
        == []
    )


def test_plan_provenance_columns_must_be_paired(client):
    headers = _auth(client)
    _, task_id, _ = _setup(client, headers)

    async def _orphan_key():
        async with TestSessionFactory() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            assert task is not None
            task.source_plan_task_key = "orphan"
            with pytest.raises(IntegrityError):
                await session.commit()

    asyncio.run(_orphan_key())
