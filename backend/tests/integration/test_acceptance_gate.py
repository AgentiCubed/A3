"""WS-4b acceptance-criteria gate: a project cannot silently close unmet.

Proves the remediation-plan WS-4(b) definition of done: a project with an
unsatisfied acceptance criterion cannot complete — closing is refused (409,
audited) until the criteria are met, or a human explicitly acknowledges the
gap, which is recorded as deliberate abandonment.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.enums import EvaluatorKind, Verdict
from app.models.agent import Agent
from app.models.audit_event import AuditEvent
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.ports import AgentRunRequest, AgentRunResult
from app.orchestration.state_machine.states import ExecutionState
from app.services import (
    artifact_service,
    closeout_service,
    execution_service,
    project_lock_service,
)
from tests.conftest import TestSessionFactory

LOCK_WAIT_PROBE_SECONDS = 0.05


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


def _project(client, headers, acceptance_criteria=None) -> dict:
    return client.post(
        "/api/v1/projects",
        json={"name": "P", "objective": "o", "acceptance_criteria": acceptance_criteria},
        headers=headers,
    ).json()


def _run_task_with_output(client, headers, pid, monkeypatch, output: str) -> None:
    """Create, assign, and inline-run one task whose execution output is fixed."""

    class _FixedOutput:
        name = "mock"

        async def run(self, request: AgentRunRequest) -> AgentRunResult:
            return AgentRunResult(output=output, provider="mock")

    monkeypatch.setattr(execution_service, "get_adapter", lambda name: _FixedOutput())
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": "Deliver"}, headers=headers
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": f"W-{uuid.uuid4().hex[:6]}", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    assert (
        client.patch(
            f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
            json={"agent_id": agent_id},
            headers=headers,
        ).status_code
        == 200
    )
    resp = client.post(f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json={}, headers=headers)
    assert resp.json()["final_state"] == "completed", resp.text


def _close(client, headers, pid, body=None):
    return client.post(f"/api/v1/projects/{pid}/close", json=body, headers=headers)


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


def _persist_acceptance_spec(project_id: str, spec: object) -> None:
    """Simulate legacy/imported JSON that bypassed the current API schema."""

    async def _update():
        async with TestSessionFactory() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            assert project is not None
            project.acceptance_criteria = spec
            await session.commit()

    asyncio.run(_update())


def _seed_evaluated_execution(project: dict, *, output: str, verdicts: list[Verdict]) -> None:
    """Store one completed execution with ordered append-only evaluations."""

    async def _seed():
        async with TestSessionFactory() as session:
            task = Task(
                organization_id=uuid.UUID(project["organization_id"]),
                project_id=uuid.UUID(project["id"]),
                title="Evaluated work",
            )
            session.add(task)
            await session.flush()
            execution = TaskExecution(
                organization_id=task.organization_id,
                task_id=task.id,
                state=ExecutionState.COMPLETED,
                output=output,
                finished_at=datetime.now(UTC),
            )
            session.add(execution)
            await session.flush()

            first_created_at = datetime.now(UTC) - timedelta(minutes=1)
            for offset, verdict in enumerate(verdicts):
                session.add(
                    Evaluation(
                        organization_id=task.organization_id,
                        task_execution_id=execution.id,
                        evaluator_kind=EvaluatorKind.DETERMINISTIC,
                        verdict=verdict,
                        score=1.0 if verdict == Verdict.PASS else 0.0,
                        summary=verdict.value,
                        created_at=first_created_at + timedelta(seconds=offset),
                    )
                )
            await session.commit()

    asyncio.run(_seed())


def test_close_refused_until_rubric_criterion_met(client, monkeypatch):
    """The WS-4b acceptance test: unmet criterion -> 409; met -> closes."""
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {
            "criteria": [
                {
                    "key": "mentions_demand_chart",
                    "check": "contains_all",
                    "params": {"keywords": ["DEMAND-CHART"]},
                }
            ]
        },
    )
    pid = project["id"]

    resp = _close(client, headers, pid)
    assert resp.status_code == 409, resp.text
    detail = resp.json()["detail"]
    assert detail["error"] == "acceptance_criteria_unmet"
    assert detail["unmet"][0]["key"] == "mentions_demand_chart"

    # The refusal changed nothing and left a trace.
    assert client.get(f"/api/v1/projects/{pid}", headers=headers).json()["status"] != "closed"
    refused = _audits(pid, "project.close_refused")
    assert len(refused) == 1
    assert refused[0]["unmet_criteria"] == ["mentions_demand_chart"]

    # Deliver work that satisfies the criterion; now the close is earned.
    _run_task_with_output(
        client, headers, pid, monkeypatch, "Attached is the DEMAND-CHART with analysis."
    )
    resp = _close(client, headers, pid)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "closed"
    assert body["closeout"]["acceptance"]["satisfied"] is True

    closed = _audits(pid, "project.closed")
    assert closed[0]["acceptance_satisfied"] is True
    assert closed[0]["unmet_criteria"] == []


def test_close_refused_until_deliverable_artifact_exists(client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    project = _project(client, headers, {"deliverables": ["demand chart"]})
    pid = project["id"]

    resp = _close(client, headers, pid)
    assert resp.status_code == 409
    assert resp.json()["detail"]["unmet"][0]["kind"] == "deliverable"

    # Store an artifact whose name matches the deliverable (separator-insensitive).
    async def _seed():
        async with TestSessionFactory() as session:
            await artifact_service.store_artifact(
                session,
                artifact_service.default_store(),
                org_id=uuid.UUID(project["organization_id"]),
                project_id=uuid.UUID(pid),
                name="widget-demand-chart.png",
                content_type="image/png",
                data=b"png-bytes",
            )
            await session.commit()

    asyncio.run(_seed())

    resp = _close(client, headers, pid)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "closed"


def test_acknowledged_close_records_deliberate_abandonment(client):
    headers = _auth(client)
    pid = _project(client, headers, {"deliverables": ["report"]})["id"]

    assert _close(client, headers, pid).status_code == 409
    resp = _close(client, headers, pid, {"acknowledge_unmet_criteria": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"

    closed = _audits(pid, "project.closed")
    assert closed[0]["unmet_criteria"] == ["report"]
    assert closed[0]["unmet_acknowledged"] is True


def test_close_waits_for_concurrent_execution_output_before_accepting(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "concise", "check": "max_length", "params": {"max": 2}}]},
    )
    _seed_evaluated_execution(project, output="OK", verdicts=[])
    task_id = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Concurrent output"},
        headers=headers,
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": "Concurrent writer", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]

    async def _race() -> None:
        async with TestSessionFactory() as writer, TestSessionFactory() as closer:
            task = await writer.get(Task, uuid.UUID(task_id))
            agent = await writer.get(Agent, uuid.UUID(agent_id))
            closing_project = await closer.get(Project, uuid.UUID(project["id"]))
            assert task is not None and agent is not None and closing_project is not None

            await execution_service._record(
                writer,
                task=task,
                agent=agent,
                attempt=1,
                state=ExecutionState.COMPLETED,
                started=datetime.now(UTC),
                output="TOO LONG",
                error=None,
                provider="mock",
                prompt_chars=1,
            )
            close_task = asyncio.create_task(
                closeout_service.close_project(
                    closer,
                    project=closing_project,
                    actor_id=None,
                )
            )
            await asyncio.sleep(LOCK_WAIT_PROBE_SECONDS)
            assert not close_task.done()

            await writer.commit()
            with pytest.raises(closeout_service.AcceptanceNotMet):
                await asyncio.wait_for(close_task, timeout=2)
            await closer.rollback()

    asyncio.run(_race())
    assert _close(client, headers, project["id"]).status_code == 409


def test_artifact_write_loses_race_to_committed_close(client, tmp_path):
    headers = _auth(client)
    project = _project(client, headers, None)

    async def _race() -> None:
        async with TestSessionFactory() as closer, TestSessionFactory() as writer:
            closing_project = await closer.get(Project, uuid.UUID(project["id"]))
            assert closing_project is not None
            close_result = await closeout_service.close_project(
                closer,
                project=closing_project,
                actor_id=None,
            )
            closeout = await closeout_service.generate_closeout(
                closer,
                org_id=uuid.UUID(project["organization_id"]),
                project_id=uuid.UUID(project["id"]),
                generated_at=datetime.now(UTC),
                acceptance=close_result.acceptance,
            )
            assert closeout["acceptance"] == close_result.acceptance.to_dict()

            artifact_task = asyncio.create_task(
                artifact_service.store_artifact(
                    writer,
                    artifact_service.LocalArtifactStore(str(tmp_path)),
                    org_id=uuid.UUID(project["organization_id"]),
                    project_id=uuid.UUID(project["id"]),
                    name="late.txt",
                    content_type="text/plain",
                    data=b"late evidence",
                )
            )
            await asyncio.sleep(LOCK_WAIT_PROBE_SECONDS)
            assert not artifact_task.done()

            await closer.commit()
            with pytest.raises(project_lock_service.ProjectClosed):
                await asyncio.wait_for(artifact_task, timeout=2)
            await writer.rollback()

    asyncio.run(_race())
    assert list(tmp_path.rglob("*")) == []


def test_close_without_criteria_is_ungated(client):
    headers = _auth(client)
    pid = _project(client, headers, None)["id"]
    resp = _close(client, headers, pid)
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"
    assert resp.json()["closeout"]["acceptance"]["evaluated"] is False


def test_malformed_acceptance_criteria_rejected_at_creation(client):
    headers = _auth(client)
    for malformed in (
        [],
        "",
        0,
        False,
        {"criteria": {"key": "x", "check": "non_empty"}},
        {"criteria": None},
        {"deliverables": "brief"},
        {"deliverables": None},
        {"deliverables": [""]},
        {"deliverables": [" _ - "]},
        {"deliverables": ["..."]},
        {"unknown_gate": []},
        {"criteria": [{"check": "unknown"}]},
        {"criteria": [{"check": "non_empty", "params": {"extra": True}}]},
        {"criteria": [{"check": "min_length", "params": {"min": "ten"}}]},
        {"criteria": [{"check": "max_length", "params": {"max": -1}}]},
        {"criteria": [{"check": "contains_all", "params": {"keywords": []}}]},
        {"criteria": [{"check": "contains_any", "params": {"keywords": [1]}}]},
        {"criteria": [{"check": "is_json", "params": {"extra": True}}]},
        {"criteria": [{"check": "regex", "params": {"pattern": "["}}]},
    ):
        resp = client.post(
            "/api/v1/projects",
            json={"name": "P", "objective": "o", "acceptance_criteria": malformed},
            headers=headers,
        )
        assert resp.status_code == 422, (malformed, resp.text)


def test_supported_acceptance_check_params_are_accepted_at_creation(client):
    headers = _auth(client)
    criteria = [
        {"check": "non_empty"},
        {"check": "min_length", "params": {"min": 1}},
        {"check": "max_length", "params": {"max": 100}},
        {"check": "contains_all", "params": {"keywords": ["alpha"]}},
        {"check": "contains_any", "params": {"keywords": ["alpha", "beta"]}},
        {"check": "is_json"},
        {"check": "regex", "params": {"pattern": "alpha+"}},
    ]

    resp = client.post(
        "/api/v1/projects",
        json={"name": "P", "objective": "o", "acceptance_criteria": {"criteria": criteria}},
        headers=headers,
    )

    assert resp.status_code == 201, resp.text


def test_malformed_persisted_acceptance_criteria_fail_closed_without_500(client):
    headers = _auth(client)
    malformed_specs = (
        [],
        "",
        0,
        False,
        {"criteria": None},
        {"deliverables": None},
        {"criteria": [{"check": "min_length", "params": {"min": "ten"}}]},
        {"criteria": [{"check": "contains_all", "params": {"keywords": [1]}}]},
        {"criteria": [{"check": "regex", "params": {"pattern": "["}}]},
    )

    for malformed in malformed_specs:
        project = _project(client, headers, None)
        _persist_acceptance_spec(project["id"], malformed)

        report_response = client.get(
            f"/api/v1/projects/{project['id']}/acceptance", headers=headers
        )
        assert report_response.status_code == 200, (malformed, report_response.text)
        report = report_response.json()
        assert report["evaluated"] is True
        assert report["satisfied"] is False
        assert report["results"][0]["key"] == "acceptance_criteria"
        assert "malformed acceptance criteria" in report["results"][0]["notes"]

        close_response = _close(client, headers, project["id"])
        assert close_response.status_code == 409, (malformed, close_response.text)


def test_separator_only_persisted_deliverable_cannot_match_unrelated_artifact(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    project = _project(client, headers, None)
    _persist_acceptance_spec(project["id"], {"deliverables": [" _ - "]})

    async def _seed_artifact():
        async with TestSessionFactory() as session:
            await artifact_service.store_artifact(
                session,
                artifact_service.default_store(),
                org_id=uuid.UUID(project["organization_id"]),
                project_id=uuid.UUID(project["id"]),
                name="unrelated-report.pdf",
                content_type="application/pdf",
                data=b"report",
            )
            await session.commit()

    asyncio.run(_seed_artifact())

    report = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers).json()
    assert report["evaluated"] is True
    assert report["satisfied"] is False
    assert report["results"][0]["key"] == "acceptance_criteria"


def test_latest_fail_evaluation_excludes_output_even_after_older_pass(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {
            "criteria": [
                {"key": "claim", "check": "contains_all", "params": {"keywords": ["CLAIM"]}}
            ]
        },
    )
    _seed_evaluated_execution(
        project, output="CLAIM appears in rejected work", verdicts=[Verdict.PASS, Verdict.FAIL]
    )

    report = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers).json()
    assert report["satisfied"] is False
    assert report["results"][0]["key"] == "claim"


def test_multiple_pass_evaluations_do_not_duplicate_output_corpus(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "length", "check": "min_length", "params": {"min": 6}}]},
    )
    _seed_evaluated_execution(project, output="1234", verdicts=[Verdict.PASS, Verdict.PASS])

    report = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers).json()
    assert report["satisfied"] is False
    assert report["results"][0]["notes"] == "length 4 < required 6"


def test_rejected_execution_output_cannot_satisfy_project_acceptance(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {
            "criteria": [
                {"key": "claim", "check": "contains_all", "params": {"keywords": ["CLAIM"]}}
            ]
        },
    )

    async def _seed_rejected_attempt():
        async with TestSessionFactory() as session:
            task = Task(
                organization_id=uuid.UUID(project["organization_id"]),
                project_id=uuid.UUID(project["id"]),
                title="Rejected work",
            )
            session.add(task)
            await session.flush()
            execution = TaskExecution(
                organization_id=task.organization_id,
                task_id=task.id,
                state=ExecutionState.COMPLETED,
                output="CLAIM appears only in rejected work",
                finished_at=datetime.now(UTC),
            )
            session.add(execution)
            await session.flush()
            session.add(
                Evaluation(
                    organization_id=task.organization_id,
                    task_execution_id=execution.id,
                    evaluator_kind=EvaluatorKind.DETERMINISTIC,
                    verdict=Verdict.FAIL,
                    score=0.0,
                    summary="rejected",
                )
            )
            await session.commit()

    asyncio.run(_seed_rejected_attempt())
    report = client.get(f"/api/v1/projects/{project['id']}/acceptance", headers=headers).json()
    assert report["satisfied"] is False
    assert report["results"][0]["key"] == "claim"


def test_acceptance_report_endpoint_shows_live_status(client, monkeypatch):
    headers = _auth(client)
    pid = _project(
        client,
        headers,
        {"criteria": [{"key": "kw", "check": "contains_all", "params": {"keywords": ["X-42"]}}]},
    )["id"]

    report = client.get(f"/api/v1/projects/{pid}/acceptance", headers=headers).json()
    assert report["evaluated"] is True
    assert report["satisfied"] is False
    assert report["results"][0] == {
        "key": "kw",
        "kind": "rubric",
        "passed": False,
        "notes": "missing keywords: ['X-42']",
    }

    _run_task_with_output(client, headers, pid, monkeypatch, "the answer is X-42 indeed")
    report = client.get(f"/api/v1/projects/{pid}/acceptance", headers=headers).json()
    assert report["satisfied"] is True
