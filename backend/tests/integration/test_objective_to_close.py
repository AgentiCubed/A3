"""Governed objective-to-close lifecycle proof.

An approved decomposition plan is the authority for execution: drafts cannot
start, materialized tasks cannot bypass project start, start is a single
audited transition, and close is earned only after governed work and acceptance
are complete.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.enums import EvaluatorKind, Verdict
from app.core.roles import ActorType
from app.evaluation.specs import normalize_rubric_specs, rubric_sha256
from app.models.audit_event import AuditEvent
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.ports import AgentRunResult
from app.orchestration.state_machine.states import ExecutionState
from app.services import (
    acceptance_service,
    closeout_service,
    decomposition_service,
    execution_service,
)
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


def _approved_project(client, headers) -> tuple[dict, dict, dict]:
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    approval = _approve(
        client,
        headers,
        project["id"],
        plan,
        _approval_payload(plan, executor),
    )
    assert approval.status_code == 200, approval.text
    return project, plan, approval.json()


def _tasks(client, headers, project_id: str) -> list[dict]:
    response = client.get(f"/api/v1/projects/{project_id}/tasks", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def _project_status(client, headers, project_id: str) -> str:
    response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["status"]


def _audits(entity_id: str, action: str) -> list[AuditEvent]:
    async def _query() -> list[AuditEvent]:
        async with TestSessionFactory() as session:
            rows = await session.execute(
                select(AuditEvent).where(
                    AuditEvent.entity_id == uuid.UUID(entity_id),
                    AuditEvent.action == action,
                )
            )
            return list(rows.scalars())

    return asyncio.run(_query())


def _tamper_materialized_task(plan_id: str) -> None:
    async def _update() -> None:
        async with TestSessionFactory() as session:
            task = await session.scalar(
                select(Task)
                .where(Task.source_plan_id == uuid.UUID(plan_id))
                .order_by(Task.order_index.desc())
            )
            assert task is not None
            task.source_plan_task_key = "tampered-plan-key"
            await session.commit()

    asyncio.run(_update())


def _set_all_task_states(project_id: str, state: ExecutionState) -> None:
    async def _update() -> None:
        async with TestSessionFactory() as session:
            rows = await session.execute(
                select(Task).where(Task.project_id == uuid.UUID(project_id))
            )
            tasks = list(rows.scalars())
            assert tasks
            for task in tasks:
                task.status = state
            await session.commit()

    asyncio.run(_update())


def _set_task_state(task_id: str, state: ExecutionState) -> None:
    async def _update() -> None:
        async with TestSessionFactory() as session:
            task = await session.get(Task, uuid.UUID(task_id))
            assert task is not None
            task.status = state
            await session.commit()

    asyncio.run(_update())


def _append_forged_passing_evidence(project_id: str, agent_id: str) -> None:
    async def _insert() -> None:
        async with TestSessionFactory() as session:
            task = await session.scalar(
                select(Task)
                .where(Task.project_id == uuid.UUID(project_id))
                .order_by(Task.order_index)
            )
            assert task is not None
            specs = normalize_rubric_specs(task.acceptance_criteria)
            rubric_hash = rubric_sha256(specs)
            timestamp = datetime(2099, 1, 1, tzinfo=UTC)
            execution = TaskExecution(
                organization_id=task.organization_id,
                task_id=task.id,
                agent_id=uuid.UUID(agent_id),
                attempt_number=99,
                state=ExecutionState.COMPLETED,
                input_context={
                    "prompt_chars": 0,
                    "evaluation": {
                        "rubric_specs": specs,
                        "rubric_sha256": rubric_hash,
                        "evaluator_agent_id": None,
                        "max_remediations": task.max_remediations,
                        "sources": ["persisted"],
                    },
                },
                output="forged passing evidence",
                provider="mock",
                started_at=timestamp,
                finished_at=timestamp,
            )
            session.add(execution)
            await session.flush()
            session.add(
                Evaluation(
                    organization_id=task.organization_id,
                    task_execution_id=execution.id,
                    evaluator_agent_id=None,
                    evaluator_kind=EvaluatorKind.DETERMINISTIC,
                    verdict=Verdict.PASS,
                    score=1.0,
                    summary="forged pass",
                    rubric_specs=specs,
                    rubric_sha256=rubric_hash,
                    rubric_source="persisted",
                )
            )
            await session.commit()

    asyncio.run(_insert())


def test_draft_plan_cannot_start(client):
    headers = _auth(client)
    project = _project(client, headers)
    _draft(client, headers, project["id"])

    response = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)

    assert response.status_code == 409, response.text
    assert _project_status(client, headers, project["id"]) == "planning"
    assert _tasks(client, headers, project["id"]) == []
    assert _audits(project["id"], "project.started") == []
    refused = _audits(project["id"], "project.start_refused")
    assert len(refused) == 1
    assert refused[0].after == {"reason": "plan_approval_required"}


def test_draft_plan_cannot_close_as_a_legacy_project(client):
    headers = _auth(client)
    project = _project(client, headers)
    _draft(client, headers, project["id"])

    response = client.post(
        f"/api/v1/projects/{project['id']}/close",
        json={"acknowledge_unmet_criteria": True},
        headers=headers,
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "plan_approval_required"
    assert _project_status(client, headers, project["id"]) == "planning"
    assert _audits(project["id"], "project.closed") == []


def test_plan_task_cannot_dispatch_before_governed_start(client):
    headers = _auth(client)
    project, plan, _ = _approved_project(client, headers)
    tasks = _tasks(client, headers, project["id"])
    task = tasks[0]

    response = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/dispatch",
        json={},
        headers=headers,
    )

    assert response.status_code == 409, response.text
    assert _project_status(client, headers, project["id"]) == "planning"
    assert _tasks(client, headers, project["id"])[0]["status"] == "planned"
    executions = client.get(
        f"/api/v1/projects/{project['id']}/tasks/{task['id']}/executions",
        headers=headers,
    )
    assert executions.status_code == 200, executions.text
    assert executions.json() == []
    refused = _audits(task["id"], "task.dispatch_refused")
    assert len(refused) == 1
    assert refused[0].after["reason"] == "governed_project_not_active"


def test_approved_plan_graph_rejects_ad_hoc_structural_edits(client):
    headers = _auth(client)
    project, plan, _ = _approved_project(client, headers)
    tasks = _tasks(client, headers, project["id"])

    added_task = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Unreviewed extra work"},
        headers=headers,
    )
    assert added_task.status_code == 409, added_task.text
    assert added_task.json()["detail"]["error"] == "approved_plan_graph_locked"

    added_dependency = client.post(
        f"/api/v1/projects/{project['id']}/dependencies",
        json={
            "predecessor_task_id": tasks[1]["id"],
            "successor_task_id": tasks[0]["id"],
        },
        headers=headers,
    )
    assert added_dependency.status_code == 409, added_dependency.text
    assert added_dependency.json()["detail"]["error"] == "approved_plan_graph_locked"
    regenerated = client.post(
        f"/api/v1/projects/{project['id']}/plans",
        json={"planner_agent_id": plan["planner_agent_id"]},
        headers=headers,
    )
    assert regenerated.status_code == 409, regenerated.text
    assert len(_tasks(client, headers, project["id"])) == len(tasks)
    refusals = _audits(project["id"], "project.graph_mutation_refused")
    assert {event.after["mutation"] for event in refusals} == {
        "task.create",
        "dependency.create",
    }


def test_governed_successor_cannot_bypass_incomplete_predecessor(client, monkeypatch):
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    tasks = {task["source_plan_task_key"]: task for task in _tasks(client, headers, project["id"])}
    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text

    response = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{tasks['deliver']['id']}/dispatch",
        json={},
        headers=headers,
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "governed_dependencies_incomplete"
    assert _tasks(client, headers, project["id"])[1]["status"] == "planned"
    refused = _audits(tasks["deliver"]["id"], "task.dispatch_refused")
    assert len(refused) == 1
    assert refused[0].after["reason"] == "governed_dependencies_incomplete"


def test_failed_governed_predecessor_requires_passing_reevaluation(client, monkeypatch):
    class _EmptyExecutor:
        name = "mock"

        async def run(self, request):
            return AgentRunResult(output="", provider="mock")

    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    monkeypatch.setattr(execution_service, "get_adapter", lambda provider: _EmptyExecutor())

    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    tasks = {task["source_plan_task_key"]: task for task in _tasks(client, headers, project["id"])}
    assert tasks["research"]["status"] == "awaiting_approval"
    assert tasks["deliver"]["status"] == "planned"

    approvals = client.get(f"/api/v1/projects/{project['id']}/approvals", headers=headers).json()
    assert len(approvals) == 1
    decided = client.post(
        f"/api/v1/projects/{project['id']}/approvals/{approvals[0]['id']}/decide",
        json={"approve": True, "comment": "Apply the remediation"},
        headers=headers,
    )
    assert decided.status_code == 200, decided.text
    refreshed = {
        task["source_plan_task_key"]: task for task in _tasks(client, headers, project["id"])
    }
    assert refreshed["research"]["status"] == "ready"

    # Even direct status corruption cannot substitute for exact PASS proof.
    _set_task_state(refreshed["research"]["id"], ExecutionState.COMPLETED)
    successor = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{refreshed['deliver']['id']}/dispatch",
        json={},
        headers=headers,
    )
    assert successor.status_code == 409, successor.text
    assert successor.json()["detail"]["error"] == "governed_dependencies_incomplete"


def test_governed_dispatch_claim_allows_one_queue_and_one_execution(client, monkeypatch):
    calls: list[str] = []

    class _CountingExecutor:
        name = "mock"

        async def run(self, request):
            calls.append(request.prompt)
            return await MockProvider().run(request)

    monkeypatch.setattr(execution_service, "get_adapter", lambda provider: _CountingExecutor())
    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)

    async def _exercise() -> None:
        project_id = uuid.UUID(project["id"])
        async with TestSessionFactory() as session:
            governed = await session.get(Project, project_id)
            assert governed is not None
            await decomposition_service.begin_project_execution(
                session,
                project=governed,
                actor_id=uuid.uuid4(),
            )
            await session.commit()

        async with TestSessionFactory() as first, TestSessionFactory() as stale:
            first_task = await first.scalar(
                select(Task).where(Task.project_id == project_id).order_by(Task.order_index)
            )
            assert first_task is not None
            stale_task = await stale.get(Task, first_task.id)
            assert stale_task is not None
            await execution_service.queue_task(
                first,
                task=first_task,
                actor_id=None,
                actor_type=ActorType.SYSTEM,
            )
            await first.commit()
            with pytest.raises(execution_service.AlreadyQueued):
                await execution_service.queue_task(
                    stale,
                    task=stale_task,
                    actor_id=None,
                    actor_type=ActorType.SYSTEM,
                )
            await stale.rollback()

        async with TestSessionFactory() as winner, TestSessionFactory() as duplicate:
            winner_task = await winner.scalar(
                select(Task).where(Task.project_id == project_id).order_by(Task.order_index)
            )
            assert winner_task is not None
            duplicate_task = await duplicate.get(Task, winner_task.id)
            assert duplicate_task is not None
            result = await execution_service.execute_task(
                winner,
                task=winner_task,
                actor_id=None,
                actor_type=ActorType.SYSTEM,
            )
            assert result.final_state == ExecutionState.COMPLETED
            await winner.commit()
            with pytest.raises(execution_service.AlreadyQueued):
                await execution_service.execute_task(
                    duplicate,
                    task=duplicate_task,
                    actor_id=None,
                    actor_type=ActorType.SYSTEM,
                )
            await duplicate.rollback()

    asyncio.run(_exercise())
    assert len(calls) == 1


def test_governed_start_is_durable_before_inline_execution(client, monkeypatch):
    async def _crash_after_start(*args, **kwargs):
        raise RuntimeError("simulated inline runtime crash")

    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    monkeypatch.setattr(
        "app.api.v1.routers.projects.scheduler_service.run_inline",
        _crash_after_start,
    )

    with pytest.raises(RuntimeError, match="simulated inline runtime crash"):
        client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)

    assert _project_status(client, headers, project["id"]) == "active"
    assert len(_audits(project["id"], "project.started")) == 1


def test_approved_plan_starts_once_and_audits_exact_plan(client, monkeypatch):
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    headers = _auth(client)
    project, plan, approval = _approved_project(client, headers)

    first = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert first.status_code == 200, first.text
    assert _project_status(client, headers, project["id"]) == "active"
    assert len(engine.calls) == 1

    second = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert second.status_code == 409, second.text
    assert len(engine.calls) == 1

    started = _audits(project["id"], "project.started")
    assert len(started) == 1
    assert started[0].before == {"status": "planning"}
    assert started[0].after["status"] == "active"
    assert started[0].after["plan_id"] == plan["id"]
    assert started[0].after["plan_version"] == plan["version"]
    assert started[0].after["plan_spec_sha256"] == plan["plan_spec_sha256"]
    assert started[0].after["materialized_task_count"] == len(approval["tasks"])


def test_materialization_corruption_blocks_start_without_partial_execution(client):
    headers = _auth(client)
    project, plan, _ = _approved_project(client, headers)
    _tamper_materialized_task(plan["id"])

    response = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)

    assert response.status_code == 409, response.text
    assert _project_status(client, headers, project["id"]) == "planning"
    assert _audits(project["id"], "project.started") == []
    for task in _tasks(client, headers, project["id"]):
        executions = client.get(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}/executions",
            headers=headers,
        )
        assert executions.status_code == 200, executions.text
        assert executions.json() == []


def test_governed_close_requires_active_project_and_every_task_complete(client, monkeypatch):
    async def _acceptance_is_satisfied(*args, **kwargs):
        return acceptance_service.AcceptanceReport(evaluated=True, satisfied=True, results=[])

    monkeypatch.setattr(
        closeout_service.acceptance_service,
        "evaluate_project_acceptance",
        _acceptance_is_satisfied,
    )
    headers = _auth(client)

    not_started, _, _ = _approved_project(client, headers)
    _set_all_task_states(not_started["id"], ExecutionState.COMPLETED)
    response = client.post(f"/api/v1/projects/{not_started['id']}/close", json={}, headers=headers)
    assert response.status_code == 409, response.text
    assert _project_status(client, headers, not_started["id"]) == "planning"

    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    incomplete, _, _ = _approved_project(client, headers)
    started = client.post(f"/api/v1/projects/{incomplete['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    assert _project_status(client, headers, incomplete["id"]) == "active"
    assert any(task["status"] != "completed" for task in _tasks(client, headers, incomplete["id"]))

    response = client.post(
        f"/api/v1/projects/{incomplete['id']}/close",
        json={"acknowledge_unmet_criteria": True},
        headers=headers,
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "plan_tasks_incomplete"
    assert _project_status(client, headers, incomplete["id"]) == "active"
    assert _audits(incomplete["id"], "project.closed") == []


def test_completed_status_without_passing_task_evidence_cannot_close(client, monkeypatch):
    engine = _CapturingEngine()
    monkeypatch.setattr("app.api.v1.routers.projects.get_workflow_engine", lambda: engine)
    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    _set_all_task_states(project["id"], ExecutionState.COMPLETED)

    response = client.post(
        f"/api/v1/projects/{project['id']}/close",
        json={"acknowledge_unmet_criteria": True},
        headers=headers,
    )

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "plan_task_evidence_invalid"
    assert _project_status(client, headers, project["id"]) == "active"
    assert _audits(project["id"], "project.closed") == []


def test_forged_pass_from_unapproved_executor_cannot_close(client):
    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    assert {task["status"] for task in _tasks(client, headers, project["id"])} == {"completed"}

    unapproved_agent = _agent(client, headers, name="Unapproved executor")
    _append_forged_passing_evidence(project["id"], unapproved_agent)

    response = client.post(f"/api/v1/projects/{project['id']}/close", json={}, headers=headers)

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "plan_task_evidence_invalid"
    assert _project_status(client, headers, project["id"]) == "active"
    assert _audits(project["id"], "project.closed") == []


def test_forged_deterministic_pass_cannot_replace_approved_evaluator(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers, name="Approved executor")
    evaluator = _agent(
        client,
        headers,
        name="Approved evaluator",
        role="evaluator",
        capabilities=("evaluation.rubric",),
    )
    payload = _approval_payload(plan, executor)
    for assignment in payload["assignments"]:
        assignment["evaluator_agent_id"] = evaluator
    approval = _approve(client, headers, project["id"], plan, payload)
    assert approval.status_code == 200, approval.text

    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    assert {task["status"] for task in _tasks(client, headers, project["id"])} == {"completed"}
    _append_forged_passing_evidence(project["id"], executor)

    response = client.post(f"/api/v1/projects/{project['id']}/close", json={}, headers=headers)

    assert response.status_code == 409, response.text
    assert response.json()["detail"]["error"] == "plan_task_evidence_invalid"
    assert _project_status(client, headers, project["id"]) == "active"


def test_governed_acceptance_cannot_be_acknowledged_away(client, monkeypatch):
    class _UnmetAcceptancePlanner:
        name = "mock"

        async def run(self, request):
            plan = json.loads(MockProvider._structured_plan(request.prompt))
            plan["project_acceptance"] = {
                "criteria": [
                    {
                        "key": "governed_evidence",
                        "check": "contains_all",
                        "params": {"keywords": ["GOVERNED-EVIDENCE-TOKEN"]},
                    }
                ],
                "deliverables": [],
            }
            return AgentRunResult(output=json.dumps(plan), provider="mock")

    monkeypatch.setattr(
        decomposition_service, "get_adapter", lambda provider: _UnmetAcceptancePlanner()
    )
    headers = _auth(client)
    project, _, _ = _approved_project(client, headers)
    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    assert {task["status"] for task in _tasks(client, headers, project["id"])} == {"completed"}

    acceptance = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers)
    assert acceptance.status_code == 200, acceptance.text
    assert acceptance.json()["satisfied"] is False

    response = client.post(
        f"/api/v1/projects/{project['id']}/close",
        json={"acknowledge_unmet_criteria": True},
        headers=headers,
    )
    assert response.status_code == 409, response.text
    assert _project_status(client, headers, project["id"]) == "active"
    assert _audits(project["id"], "project.closed") == []


def test_successful_objective_to_close_uses_one_governed_start(client):
    headers = _auth(client)
    project, plan, _ = _approved_project(client, headers)
    assert _project_status(client, headers, project["id"]) == "planning"

    started = client.post(f"/api/v1/projects/{project['id']}/start", json={}, headers=headers)
    assert started.status_code == 200, started.text
    assert _project_status(client, headers, project["id"]) == "active"
    tasks = _tasks(client, headers, project["id"])
    assert {task["status"] for task in tasks} == {"completed"}
    for task in tasks:
        evaluations = client.get(
            f"/api/v1/projects/{project['id']}/tasks/{task['id']}/evaluations",
            headers=headers,
        )
        assert evaluations.status_code == 200, evaluations.text
        assert len(evaluations.json()) == 1
        assert evaluations.json()[0]["verdict"] == "pass"
        assert evaluations.json()[0]["rubric_source"] == "persisted"

    acceptance = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers)
    assert acceptance.status_code == 200, acceptance.text
    assert acceptance.json()["evaluated"] is True
    assert acceptance.json()["satisfied"] is True

    closed = client.post(f"/api/v1/projects/{project['id']}/close", json={}, headers=headers)
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "closed"
    assert closed.json()["closeout"]["acceptance"]["satisfied"] is True
    assert _project_status(client, headers, project["id"]) == "closed"

    assert len(_audits(plan["id"], "plan.generated")) == 1
    assert len(_audits(plan["id"], "plan.approved")) == 1
    assert len(_audits(project["id"], "project.started")) == 1
    closed_audits = _audits(project["id"], "project.closed")
    assert len(closed_audits) == 1
    assert closed_audits[0].after["all_plan_tasks_completed"] is True
    assert set(closed_audits[0].after["task_evaluation_ids"]) == {
        task["source_plan_task_key"] for task in tasks
    }
