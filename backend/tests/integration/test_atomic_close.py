"""Issue #45: project closure is atomic with acceptance-changing writes."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.core.artifacts import LocalArtifactStore
from app.models.agent import Agent
from app.models.artifact import Artifact
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.ports import AgentRunResult
from app.orchestration.state_machine.states import ExecutionState
from app.services import (
    acceptance_boundary_service,
    acceptance_service,
    artifact_service,
    closeout_service,
    evaluation_service,
    execution_service,
)
from tests.conftest import TestSessionFactory
from tests.integration.test_acceptance_gate import (
    _audits,
    _auth,
    _close,
    _project,
    _run_task_with_output,
)


def test_close_serializes_with_concurrent_execution_output(client, monkeypatch):
    """A real second SQLite connection cannot commit output behind close."""
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "bounded", "check": "max_length", "params": {"max": 20}}]},
    )
    project_id = uuid.UUID(project["id"])
    _run_task_with_output(client, headers, project["id"], monkeypatch, "short")

    real_evaluate = acceptance_service.evaluate_project_acceptance
    close_evaluated = asyncio.Event()
    release_close = asyncio.Event()

    async def _pause_after_evaluation(*args, **kwargs):
        report = await real_evaluate(*args, **kwargs)
        assert report.satisfied is True
        close_evaluated.set()
        await release_close.wait()
        return report

    monkeypatch.setattr(
        acceptance_service,
        "evaluate_project_acceptance",
        _pause_after_evaluation,
    )

    async def _race() -> tuple[str, int, dict | None]:
        # Detached rows let the writer's new connection make the guarded project
        # UPDATE its first database statement, matching the production writer.
        async with TestSessionFactory() as preload:
            task = await preload.scalar(select(Task).where(Task.project_id == project_id))
            assert task is not None
            execution = await preload.scalar(
                select(TaskExecution).where(TaskExecution.task_id == task.id)
            )
            assert execution is not None
            agent = await preload.get(Agent, execution.agent_id)
            assert agent is not None

        async def _close() -> None:
            async with TestSessionFactory() as session:
                current = await session.get(Project, project_id)
                assert current is not None
                await closeout_service.close_project(
                    session,
                    project=current,
                    actor_id=None,
                )
                await session.commit()

        async def _late_output() -> str:
            await close_evaluated.wait()
            async with TestSessionFactory() as session:
                try:
                    await execution_service._record(
                        session,
                        task=task,
                        agent=agent,
                        attempt=2,
                        state=ExecutionState.COMPLETED,
                        started=datetime.now(UTC),
                        output="this late output would make the accepted corpus too long",
                        error=None,
                        provider="mock",
                        prompt_chars=1,
                    )
                    await session.commit()
                except acceptance_boundary_service.ProjectClosed:
                    await session.rollback()
                    return "rejected"
            return "committed"

        close_task = asyncio.create_task(_close())
        await close_evaluated.wait()
        writer_task = asyncio.create_task(_late_output())
        await asyncio.sleep(0.05)
        assert writer_task.done() is False
        release_close.set()
        await close_task
        assert await writer_task == "rejected"

        async with TestSessionFactory() as verify:
            current = await verify.get(Project, project_id)
            assert current is not None
            execution_count = int(
                await verify.scalar(
                    select(func.count(TaskExecution.id))
                    .join(Task, TaskExecution.task_id == Task.id)
                    .where(Task.project_id == project_id)
                )
                or 0
            )
            return current.status.value, execution_count, current.closure_acceptance

    status_value, execution_count, closure_acceptance = asyncio.run(_race())
    assert status_value == "closed"
    assert execution_count == 1
    assert closure_acceptance is not None
    assert closure_acceptance["satisfied"] is True


def test_close_first_rejects_concurrent_artifact_before_filesystem_write(
    client, monkeypatch, tmp_path
):
    headers = _auth(client)
    project = _project(client, headers, None)
    project_id = uuid.UUID(project["id"])
    close_evaluated = asyncio.Event()
    release_close = asyncio.Event()
    real_evaluate = acceptance_service.evaluate_project_acceptance

    async def _pause_after_evaluation(*args, **kwargs):
        report = await real_evaluate(*args, **kwargs)
        close_evaluated.set()
        await release_close.wait()
        return report

    monkeypatch.setattr(
        acceptance_service,
        "evaluate_project_acceptance",
        _pause_after_evaluation,
    )

    async def _race() -> str:
        async def _close() -> None:
            async with TestSessionFactory() as session:
                current = await session.get(Project, project_id)
                assert current is not None
                await closeout_service.close_project(
                    session,
                    project=current,
                    actor_id=None,
                )
                await session.commit()

        async def _late_artifact() -> str:
            await close_evaluated.wait()
            async with TestSessionFactory() as session:
                try:
                    await artifact_service.store_artifact(
                        session,
                        LocalArtifactStore(str(tmp_path)),
                        org_id=uuid.UUID(project["organization_id"]),
                        project_id=project_id,
                        name="late.txt",
                        content_type="text/plain",
                        data=b"late",
                    )
                    await session.commit()
                except acceptance_boundary_service.ProjectClosed:
                    await session.rollback()
                    return "rejected"
            return "committed"

        close_task = asyncio.create_task(_close())
        await close_evaluated.wait()
        artifact_task = asyncio.create_task(_late_artifact())
        await asyncio.sleep(0.05)
        assert artifact_task.done() is False
        release_close.set()
        await close_task
        return await artifact_task

    assert asyncio.run(_race()) == "rejected"
    assert list(tmp_path.rglob("*")) == []
    assert client.get(f"/api/v1/projects/{project['id']}/artifacts", headers=headers).json() == []


def test_artifact_first_commits_before_close_evaluates(client, monkeypatch, tmp_path):
    headers = _auth(client)
    project = _project(client, headers, {"deliverables": ["report"]})
    project_id = uuid.UUID(project["id"])
    writer_claimed = asyncio.Event()
    release_writer = asyncio.Event()
    real_claim = acceptance_boundary_service.claim_acceptance_write

    async def _pause_after_claim(*args, **kwargs):
        revision = await real_claim(*args, **kwargs)
        writer_claimed.set()
        await release_writer.wait()
        return revision

    monkeypatch.setattr(
        acceptance_boundary_service,
        "claim_acceptance_write",
        _pause_after_claim,
    )

    async def _race() -> tuple[dict, int]:
        async with TestSessionFactory() as preload:
            detached_project = await preload.get(Project, project_id)
            assert detached_project is not None
            preload.expunge(detached_project)

        async def _artifact() -> None:
            async with TestSessionFactory() as session:
                await artifact_service.store_artifact(
                    session,
                    LocalArtifactStore(str(tmp_path)),
                    org_id=uuid.UUID(project["organization_id"]),
                    project_id=project_id,
                    name="final-report.md",
                    content_type="text/markdown",
                    data=b"report",
                )
                await session.commit()

        async def _close() -> None:
            async with TestSessionFactory() as session:
                session.add(detached_project)
                await closeout_service.close_project(
                    session,
                    project=detached_project,
                    actor_id=None,
                )
                await session.commit()

        artifact_task = asyncio.create_task(_artifact())
        await writer_claimed.wait()
        close_task = asyncio.create_task(_close())
        await asyncio.sleep(0.05)
        assert close_task.done() is False
        release_writer.set()
        await artifact_task
        await close_task

        async with TestSessionFactory() as verify:
            current = await verify.get(Project, project_id)
            assert current is not None
            artifact_count = int(
                await verify.scalar(
                    select(func.count(Artifact.id)).where(Artifact.project_id == project_id)
                )
                or 0
            )
            assert current.closure_acceptance is not None
            return current.closure_acceptance, artifact_count

    closure_acceptance, artifact_count = asyncio.run(_race())
    assert closure_acceptance["satisfied"] is True
    assert artifact_count == 1
    assert len([path for path in tmp_path.rglob("*") if path.is_file()]) == 1


def test_close_cancels_running_legacy_task_and_rejects_its_late_output(client, monkeypatch):
    headers = _auth(client)
    project = _project(client, headers, None)
    project_id = uuid.UUID(project["id"])
    task_id = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Slow work"},
        headers=headers,
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": f"Slow-{uuid.uuid4().hex[:6]}", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    assigned = client.patch(
        f"/api/v1/projects/{project['id']}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    assert assigned.status_code == 200, assigned.text

    provider_started = asyncio.Event()
    release_provider = asyncio.Event()

    class _BlockingProvider:
        name = "mock"

        async def run(self, request):  # noqa: ARG002
            provider_started.set()
            await release_provider.wait()
            return AgentRunResult(output="late output", provider="mock")

    monkeypatch.setattr(execution_service, "get_adapter", lambda provider: _BlockingProvider())

    async def _race() -> tuple[str, str, int]:
        async def _execute() -> str:
            async with TestSessionFactory() as session:
                task = await session.get(Task, uuid.UUID(task_id))
                assert task is not None
                try:
                    await execution_service.execute_task(session, task=task)
                    await session.commit()
                except execution_service.ProjectClosed:
                    await session.rollback()
                    return "rejected"
            return "committed"

        execution_task = asyncio.create_task(_execute())
        await provider_started.wait()

        async with TestSessionFactory() as close_session:
            current = await close_session.get(Project, project_id)
            assert current is not None
            await closeout_service.close_project(
                close_session,
                project=current,
                actor_id=None,
            )
            await close_session.commit()

        release_provider.set()
        assert await execution_task == "rejected"

        async with TestSessionFactory() as verify:
            current = await verify.get(Project, project_id)
            task = await verify.get(Task, uuid.UUID(task_id))
            assert current is not None
            assert task is not None
            execution_count = int(
                await verify.scalar(
                    select(func.count(TaskExecution.id)).where(
                        TaskExecution.task_id == uuid.UUID(task_id)
                    )
                )
                or 0
            )
            return current.status.value, task.status.value, execution_count

    project_status, task_status, execution_count = asyncio.run(_race())
    assert project_status == "closed"
    assert task_status == "cancelled"
    assert execution_count == 0


def test_stale_acceptance_snapshot_cannot_commit_close(client, monkeypatch):
    """Two-session interleaving rejects a snapshot made stale by a later output."""
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "bounded", "check": "max_length", "params": {"max": 10}}]},
    )
    project_id = uuid.UUID(project["id"])
    _run_task_with_output(client, headers, project["id"], monkeypatch, "ok")

    async def _capture_snapshot() -> tuple[int, str, dict]:
        async with TestSessionFactory() as session:
            current = await session.get(Project, project_id)
            assert current is not None
            report = await acceptance_service.evaluate_project_acceptance(
                session,
                project=current,
            )
            assert report.satisfied is True
            return current.acceptance_revision, current.status.value, report.to_dict()

    stale_revision, stale_status, stale_report = asyncio.run(_capture_snapshot())

    # A separate request commits contradictory evidence after the first session
    # evaluated acceptance but before it attempts the close compare-and-set.
    _run_task_with_output(
        client,
        headers,
        project["id"],
        monkeypatch,
        "this later output makes the combined corpus too long",
    )
    assert (
        client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers).json()[
            "satisfied"
        ]
        is False
    )

    async def _attempt_stale_close() -> None:
        async with TestSessionFactory() as session:
            current = await session.get(Project, project_id)
            assert current is not None
            assert current.status.value == stale_status
            assert current.acceptance_revision > stale_revision
            with pytest.raises(closeout_service.AcceptanceSnapshotChanged):
                await closeout_service._commit_close_snapshot(
                    session,
                    project=current,
                    acceptance_revision=stale_revision,
                    acceptance_snapshot={
                        **stale_report,
                        "acceptance_revision": stale_revision,
                    },
                )
            await session.rollback()

    asyncio.run(_attempt_stale_close())
    assert (
        client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()["status"]
        != "closed"
    )
    assert _close(client, headers, project["id"]).status_code == 409


def test_closed_project_rejects_late_evidence_and_reuses_authorizing_snapshot(
    client, monkeypatch, tmp_path
):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "bounded", "check": "max_length", "params": {"max": 20}}]},
    )
    project_id = uuid.UUID(project["id"])
    _run_task_with_output(client, headers, project["id"], monkeypatch, "short")

    real_evaluate = acceptance_service.evaluate_project_acceptance
    evaluation_calls = 0

    async def _counted_evaluate(*args, **kwargs):
        nonlocal evaluation_calls
        evaluation_calls += 1
        return await real_evaluate(*args, **kwargs)

    monkeypatch.setattr(acceptance_service, "evaluate_project_acceptance", _counted_evaluate)
    response = _close(client, headers, project["id"])
    assert response.status_code == 200, response.text
    acceptance_snapshot = response.json()["closeout"]["acceptance"]
    assert acceptance_snapshot["satisfied"] is True
    assert acceptance_snapshot["acceptance_revision"] >= 1
    assert evaluation_calls == 1

    closed_audit = _audits(project["id"], "project.closed")[0]
    assert closed_audit["acceptance"] == acceptance_snapshot
    assert closed_audit["acceptance_revision"] == acceptance_snapshot["acceptance_revision"]

    async def _attempt_late_writes() -> tuple[tuple[int, int, int], tuple[int, int, int]]:
        async with TestSessionFactory() as session:
            task = await session.scalar(select(Task).where(Task.project_id == project_id))
            assert task is not None
            execution = await session.scalar(
                select(TaskExecution).where(TaskExecution.task_id == task.id)
            )
            assert execution is not None
            agent = await session.get(Agent, execution.agent_id)
            assert agent is not None

            async def _counts() -> tuple[int, int, int]:
                return (
                    int(
                        await session.scalar(
                            select(func.count(TaskExecution.id))
                            .join(Task, TaskExecution.task_id == Task.id)
                            .where(Task.project_id == project_id)
                        )
                        or 0
                    ),
                    int(
                        await session.scalar(
                            select(func.count(Evaluation.id))
                            .join(TaskExecution, Evaluation.task_execution_id == TaskExecution.id)
                            .join(Task, TaskExecution.task_id == Task.id)
                            .where(Task.project_id == project_id)
                        )
                        or 0
                    ),
                    int(
                        await session.scalar(
                            select(func.count(Artifact.id)).where(Artifact.project_id == project_id)
                        )
                        or 0
                    ),
                )

            before = await _counts()
            with pytest.raises(acceptance_boundary_service.ProjectClosed):
                await execution_service._record(
                    session,
                    task=task,
                    agent=agent,
                    attempt=2,
                    state=ExecutionState.COMPLETED,
                    started=datetime.now(UTC),
                    output="this contradictory execution is longer than twenty characters",
                    error=None,
                    provider="mock",
                    prompt_chars=1,
                )
            with pytest.raises(acceptance_boundary_service.ProjectClosed):
                await evaluation_service.evaluate_execution(
                    session,
                    execution=execution,
                    rubric_specs=[{"key": "reject", "check": "max_length", "params": {"max": 0}}],
                    evaluator_agent=None,
                    rubric_source="test",
                    actor_id=None,
                )
            with pytest.raises(acceptance_boundary_service.ProjectClosed):
                await artifact_service.store_artifact(
                    session,
                    LocalArtifactStore(str(tmp_path)),
                    org_id=uuid.UUID(project["organization_id"]),
                    project_id=project_id,
                    name="late.txt",
                    content_type="text/plain",
                    data=b"late",
                )
            after = await _counts()
            await session.rollback()
            return before, after

    before, after = asyncio.run(_attempt_late_writes())
    assert after == before
    assert list(tmp_path.rglob("*")) == []

    task_id = client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()[0]["id"]
    dispatch = client.post(
        f"/api/v1/projects/{project['id']}/tasks/{task_id}/dispatch",
        json={},
        headers=headers,
    )
    assert dispatch.status_code == 409
    assert dispatch.json()["detail"]["error"] == "project_closed"

    later_closeout = client.get(
        f"/api/v1/projects/{project['id']}/closeout", headers=headers
    ).json()
    assert later_closeout["acceptance"] == acceptance_snapshot
    assert evaluation_calls == 1


def test_atomic_boundary_preserves_acknowledged_abandonment(client):
    headers = _auth(client)
    project = _project(client, headers, {"deliverables": ["report"]})

    response = _close(
        client,
        headers,
        project["id"],
        {"acknowledge_unmet_criteria": True},
    )
    assert response.status_code == 200, response.text
    acceptance_snapshot = response.json()["closeout"]["acceptance"]
    assert acceptance_snapshot["satisfied"] is False

    closed_audit = _audits(project["id"], "project.closed")[0]
    assert closed_audit["unmet_criteria"] == ["report"]
    assert closed_audit["unmet_acknowledged"] is True
    assert closed_audit["acceptance"] == acceptance_snapshot
