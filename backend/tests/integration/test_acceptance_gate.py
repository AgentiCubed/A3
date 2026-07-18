"""WS-4b acceptance-criteria gate: a project cannot silently close unmet.

Proves the remediation-plan WS-4(b) definition of done: a project with an
unsatisfied acceptance criterion cannot complete — closing is refused (409,
audited) until the criteria are met, or a human explicitly acknowledges the
gap, which is recorded as deliberate abandonment.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.enums import EvaluatorKind, Verdict
from app.models.audit_event import AuditEvent
from app.models.evaluation import Evaluation
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.ports import AgentRunRequest, AgentRunResult
from app.orchestration.state_machine.states import ExecutionState
from app.services import artifact_service, execution_service
from tests.conftest import TestSessionFactory


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
        {"criteria": {"key": "x", "check": "non_empty"}},
        {"deliverables": "brief"},
        {"unknown_gate": []},
    ):
        resp = client.post(
            "/api/v1/projects",
            json={"name": "P", "objective": "o", "acceptance_criteria": malformed},
            headers=headers,
        )
        assert resp.status_code == 422, (malformed, resp.text)


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
