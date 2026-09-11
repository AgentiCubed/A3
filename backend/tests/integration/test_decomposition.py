"""WS-6A: objective-to-plan drafts are strict, durable, and non-executable."""

from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.enums import AgentStatus, ProjectStatus
from app.models.agent import Agent
from app.models.audit_event import AuditEvent
from app.models.decomposition_plan import DecompositionPlan
from app.models.project import Project
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import (
    AgentRunResult,
    ProviderCallError,
    ProviderErrorCategory,
    parse_provider_diagnostic,
)
from app.services import decomposition_service
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"plan-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _project(client, headers, objective="Produce an evidence-backed market brief") -> dict:
    return client.post(
        "/api/v1/projects",
        json={"name": "Plan me", "objective": objective},
        headers=headers,
    ).json()


def _planner(client, headers, provider: str = "mock") -> str:
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": "Planner", "kind": "ai", "provider": provider, "model": "mock-plan"},
        headers=headers,
    ).json()["id"]
    response = client.post(
        f"/api/v1/agents/{agent_id}/capabilities",
        json={"capability": "planning.decompose", "proficiency": 4},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return agent_id


def _generate(client, headers, project_id, planner_id):
    return client.post(
        f"/api/v1/projects/{project_id}/plans",
        json={"planner_agent_id": planner_id},
        headers=headers,
    )


def _set_project_status(project_id: str, status: ProjectStatus) -> None:
    import asyncio

    async def _update():
        async with TestSessionFactory() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            assert project is not None
            project.status = status
            await session.commit()

    asyncio.run(_update())


def _set_agent_status(agent_id: str, status: AgentStatus) -> None:
    import asyncio

    async def _update():
        async with TestSessionFactory() as session:
            agent = await session.get(Agent, uuid.UUID(agent_id))
            assert agent is not None
            agent.status = status
            await session.commit()

    asyncio.run(_update())


def _audits(entity_id: str) -> list[AuditEvent]:
    import asyncio

    async def _query():
        async with TestSessionFactory() as session:
            rows = await session.execute(
                select(AuditEvent)
                .where(AuditEvent.entity_id == uuid.UUID(entity_id))
                .order_by(AuditEvent.occurred_at, AuditEvent.id)
            )
            return list(rows.scalars().all())

    return asyncio.run(_query())


def test_objective_generates_durable_draft_without_tasks(client):
    headers = _auth(client)
    project = _project(client, headers)
    response = _generate(client, headers, project["id"], _planner(client, headers))
    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan["status"] == "draft"
    assert plan["version"] == 1
    assert len(plan["objective_sha256"]) == 64
    assert len(plan["plan_spec_sha256"]) == 64
    assert len(plan["provider_output_sha256"]) == 64
    assert plan["provider_output_chars"] > 0
    assert [task["key"] for task in plan["plan_spec"]["tasks"]] == ["research", "deliver"]
    assert plan["plan_spec"]["dependencies"] == [
        {
            "predecessor_key": "research",
            "successor_key": "deliver",
            "dependency_type": "finish_to_start",
            "lag_hours": 0.0,
        }
    ]
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    stored = client.get(
        f"/api/v1/projects/{project['id']}/plans/{plan['id']}", headers=headers
    ).json()
    assert stored["plan_spec"] == plan["plan_spec"]
    assert client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()["status"] == (
        "planning"
    )


def test_malformed_planner_output_is_stored_invalid_and_never_creates_tasks(client):
    headers = _auth(client)
    project = _project(client, headers, "[[MALFORMED_PLAN]] produce a brief")
    response = _generate(client, headers, project["id"], _planner(client, headers))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "plan_generation_failed"

    plans = client.get(f"/api/v1/projects/{project['id']}/plans", headers=headers).json()
    assert len(plans) == 1
    assert plans[0]["id"] == detail["plan_id"]
    assert plans[0]["status"] == "invalid"
    assert plans[0]["version"] == 1
    assert plans[0]["error_code"] == "invalid_plan"
    assert "not valid JSON" in plans[0]["diagnostic"]
    assert len(plans[0]["provider_output_sha256"]) == 64
    assert plans[0]["provider_output_chars"] > 0
    assert "raw_output" not in plans[0]
    assert client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()["status"] == (
        "intake"
    )
    failed_events = [
        event for event in _audits(plans[0]["id"]) if event.action == "plan.generation_failed"
    ]
    assert len(failed_events) == 1
    assert failed_events[0].after["provider_output_sha256"] == plans[0]["provider_output_sha256"]
    assert failed_events[0].after["provider_output_chars"] == plans[0]["provider_output_chars"]
    assert "diagnostic" not in failed_events[0].after
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


@pytest.mark.parametrize(
    "mutation,error",
    [
        (
            lambda plan: plan["dependencies"].append(
                {"predecessor_key": "deliver", "successor_key": "research"}
            ),
            "cycle",
        ),
        (lambda plan: plan["tasks"].append(dict(plan["tasks"][0])), "unique"),
        (
            lambda plan: plan["tasks"][0].update(required_capabilities=["unknown.capability"]),
            "unknown capabilities",
        ),
        (
            lambda plan: plan["project_acceptance"].update(criteria=[], deliverables=[]),
            "must define",
        ),
    ],
)
def test_invalid_plan_contracts_fail_closed(client, monkeypatch, mutation, error):
    headers = _auth(client)
    project = _project(client, headers)
    planner_id = _planner(client, headers)

    class _InvalidPlanner:
        name = "invalid"

        async def run(self, request):
            raw = json.loads(MockProvider._structured_plan(request.prompt))
            mutation(raw)
            return AgentRunResult(output=json.dumps(raw), provider="invalid")

    monkeypatch.setattr(decomposition_service, "get_adapter", lambda provider: _InvalidPlanner())
    response = _generate(client, headers, project["id"], planner_id)
    assert response.status_code == 422
    assert error in response.json()["detail"]["detail"].lower()
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].update(
            check="min_length", params={"min": "bad"}
        ),
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].update(
            check="contains_all", params={"keywords": "abc"}
        ),
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].update(
            check="contains_all", params={"keywords": [1]}
        ),
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].update(
            check="regex", params={"pattern": "safe-looking.*"}
        ),
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].update(weight="Infinity"),
        lambda plan: plan["tasks"][0]["acceptance_criteria"].append(
            dict(plan["tasks"][0]["acceptance_criteria"][0])
        ),
        lambda plan: plan["tasks"][0]["acceptance_criteria"][0].pop("key"),
    ],
)
def test_generated_plan_rejects_non_executable_rubrics(client, monkeypatch, mutation):
    headers = _auth(client)
    project = _project(client, headers)
    planner_id = _planner(client, headers)

    class _InvalidPlanner:
        name = "invalid"

        async def run(self, request):
            raw = json.loads(MockProvider._structured_plan(request.prompt))
            mutation(raw)
            return AgentRunResult(output=json.dumps(raw), provider="invalid")

    monkeypatch.setattr(decomposition_service, "get_adapter", lambda provider: _InvalidPlanner())
    response = _generate(client, headers, project["id"], planner_id)
    assert response.status_code == 422, response.text
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


@pytest.mark.parametrize(
    "mutation",
    [
        lambda dependency: dependency.update(dependency_type="start_to_start"),
        lambda dependency: dependency.update(lag_hours=1),
    ],
)
def test_generated_plan_rejects_unsupported_runtime_dependency_semantics(
    client, monkeypatch, mutation
):
    headers = _auth(client)
    project = _project(client, headers)
    planner_id = _planner(client, headers)

    class _InvalidPlanner:
        name = "invalid"

        async def run(self, request):
            raw = json.loads(MockProvider._structured_plan(request.prompt))
            mutation(raw["dependencies"][0])
            return AgentRunResult(output=json.dumps(raw), provider="invalid")

    monkeypatch.setattr(decomposition_service, "get_adapter", lambda provider: _InvalidPlanner())
    response = _generate(client, headers, project["id"], planner_id)
    assert response.status_code == 422, response.text
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


def test_closed_project_cannot_be_reopened_by_plan_generation(client):
    headers = _auth(client)
    project = _project(client, headers)
    planner_id = _planner(client, headers)
    _set_project_status(project["id"], ProjectStatus.CLOSED)

    response = _generate(client, headers, project["id"], planner_id)
    assert response.status_code == 409
    assert client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()["status"] == (
        "closed"
    )
    assert client.get(f"/api/v1/projects/{project['id']}/plans", headers=headers).json() == []


def test_planner_must_be_same_org_active_ai_with_decompose_capability(client, monkeypatch):
    monkeypatch.setattr(
        decomposition_service,
        "get_adapter",
        lambda provider: (_ for _ in ()).throw(AssertionError("ineligible planner was invoked")),
    )
    headers = _auth(client)
    project = _project(client, headers)

    missing_capability = client.post(
        "/api/v1/agents",
        json={"name": "No capability", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    assert _generate(client, headers, project["id"], missing_capability).status_code == 422

    human = client.post(
        "/api/v1/agents",
        json={"name": "Human", "kind": "human", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/agents/{human}/capabilities",
        json={"capability": "planning.decompose"},
        headers=headers,
    )
    assert _generate(client, headers, project["id"], human).status_code == 422

    disabled = _planner(client, headers)
    _set_agent_status(disabled, AgentStatus.DISABLED)
    assert _generate(client, headers, project["id"], disabled).status_code == 422

    other_headers = _auth(client)
    other_planner = _planner(client, other_headers)
    assert _generate(client, headers, project["id"], other_planner).status_code == 404
    assert client.get(f"/api/v1/projects/{project['id']}/plans", headers=headers).json() == []


def test_plan_lifecycle_events_are_audited_and_versions_advance(client):
    headers = _auth(client)
    project = _project(client, headers)
    planner_id = _planner(client, headers)
    plan = _generate(client, headers, project["id"], planner_id).json()

    generated = [event for event in _audits(plan["id"]) if event.action == "plan.generated"]
    assert len(generated) == 1
    assert generated[0].after["version"] == 1
    assert generated[0].after["plan_spec_sha256"] == plan["plan_spec_sha256"]
    status_events = [
        event for event in _audits(project["id"]) if event.action == "project.status_changed"
    ]
    assert len(status_events) == 1
    assert status_events[0].before == {"status": "intake"}
    assert status_events[0].after["status"] == "planning"

    rejected = client.post(
        f"/api/v1/projects/{project['id']}/plans/{plan['id']}/reject",
        json={"comment": "Revise the scope"},
        headers=headers,
    )
    assert rejected.status_code == 200
    rejection_events = [event for event in _audits(plan["id"]) if event.action == "plan.rejected"]
    assert len(rejection_events) == 1
    assert rejection_events[0].after["comment"] == "Revise the scope"

    replacement = _generate(client, headers, project["id"], planner_id)
    assert replacement.status_code == 201, replacement.text
    assert replacement.json()["version"] == 2


async def test_database_enforces_one_active_draft_per_project(client, session):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _generate(client, headers, project["id"], _planner(client, headers)).json()

    duplicate = DecompositionPlan(
        organization_id=uuid.UUID(project["organization_id"]),
        project_id=uuid.UUID(project["id"]),
        planner_agent_id=uuid.UUID(plan["planner_agent_id"]),
        contract_version=plan["contract_version"],
        version=2,
        objective=plan["objective"],
        objective_sha256=plan["objective_sha256"],
        status="draft",
        plan_spec=plan["plan_spec"],
        plan_spec_sha256=plan["plan_spec_sha256"],
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()


def test_rejected_draft_never_materializes_and_cannot_be_decided_twice(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _generate(client, headers, project["id"], _planner(client, headers)).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/plans/{plan['id']}/reject",
        json={"comment": "Revise the scope"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    again = client.post(
        f"/api/v1/projects/{project['id']}/plans/{plan['id']}/reject",
        json={},
        headers=headers,
    )
    assert again.status_code == 409


def test_provider_failure_records_status_and_category_not_just_a_class_name(client, monkeypatch):
    """A dead endpoint and a malformed plan must not read identically.

    GitHub Models' 2026-07-30 retirement returned 410 Gone, but the planner's
    broad handler recorded only ``planner failed with ProviderCallError`` —
    discarding the status that distinguishes "the endpoint is gone" from "the
    model wrote bad JSON". Three misdiagnoses followed. The status/category
    must reach the stored diagnostic that the API returns.
    """

    class _GoneProvider:
        name = "gemini"

        async def run(self, request):
            raise ProviderCallError(
                http_status=410,
                category=ProviderErrorCategory.NOT_FOUND,
            )

    monkeypatch.setattr(decomposition_service, "get_adapter", lambda provider: _GoneProvider())
    headers = _auth(client)
    project = _project(client, headers, "produce a brief")
    response = _generate(client, headers, project["id"], _planner(client, headers))
    assert response.status_code == 422

    plans = client.get(f"/api/v1/projects/{project['id']}/plans", headers=headers).json()
    assert plans[0]["error_code"] == "planner_error"
    diagnostic = plans[0]["diagnostic"]
    assert "provider_http_status=410" in diagnostic
    assert "provider_error_category=not_found" in diagnostic
    assert "Model or endpoint not found" in diagnostic
    # A truncation failure remains distinguishable: it stores output, this
    # does not reach the model at all.
    assert plans[0]["provider_output_chars"] == 0


def test_retired_provider_diagnostic_names_the_replacement(client, monkeypatch):
    """An agent still pointing at a retired provider gets migration guidance."""
    monkeypatch.setattr(
        decomposition_service,
        "get_adapter",
        lambda provider: get_adapter("github_models"),
    )
    headers = _auth(client)
    project = _project(client, headers, "produce a brief")
    _generate(client, headers, project["id"], _planner(client, headers, provider="github_models"))

    plans = client.get(f"/api/v1/projects/{project['id']}/plans", headers=headers).json()
    diagnostic = plans[0]["diagnostic"]
    assert "provider_http_status=410" in diagnostic
    assert "retired on 2026-07-30" in diagnostic
    assert "gemini" in diagnostic
    assert parse_provider_diagnostic(diagnostic) == (410, "not_found")
