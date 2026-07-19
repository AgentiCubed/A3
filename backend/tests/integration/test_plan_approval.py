"""WS-6B: explicit approval atomically materializes the reviewed plan."""

from __future__ import annotations

import asyncio
import json
import uuid

from sqlalchemy import select

from app.core.enums import AgentStatus
from app.models.agent import Agent
from app.models.audit_event import AuditEvent
from app.models.decomposition_plan import DecompositionPlan
from app.models.project import Project
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.ports import AgentRunResult
from app.services import decomposition_service
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"approve-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _project(client, headers, acceptance=None) -> dict:
    payload = {"name": "Governed project", "objective": "Produce an evidence-backed brief"}
    if acceptance is not None:
        payload["acceptance_criteria"] = acceptance
    response = client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def _agent(client, headers, *, name="Executor", kind="ai", role="executor", capabilities=()) -> str:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": name,
            "kind": kind,
            "provider": "mock",
            "model": "mock",
            "default_role": role,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    agent_id = response.json()["id"]
    for capability in capabilities:
        added = client.post(
            f"/api/v1/agents/{agent_id}/capabilities",
            json={"capability": capability, "proficiency": 4},
            headers=headers,
        )
        assert added.status_code == 201, added.text
    return agent_id


def _draft(client, headers, project_id: str) -> dict:
    planner = _agent(
        client,
        headers,
        name="Planner",
        role="either",
        capabilities=("planning.decompose",),
    )
    response = client.post(
        f"/api/v1/projects/{project_id}/plans",
        json={"planner_agent_id": planner},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _approval_payload(plan: dict, agent_id: str, **overrides) -> dict:
    assignments = [
        {"task_key": task["key"], "agent_id": agent_id} for task in plan["plan_spec"]["tasks"]
    ]
    payload = {
        "expected_version": plan["version"],
        "expected_plan_spec_sha256": plan["plan_spec_sha256"],
        "assignments": assignments,
        "comment": "Approved exact reviewed plan",
    }
    payload.update(overrides)
    return payload


def _approve(client, headers, project_id: str, plan: dict, payload: dict):
    return client.post(
        f"/api/v1/projects/{project_id}/plans/{plan['id']}/approve",
        json=payload,
        headers=headers,
    )


def _mutate_project(project_id: str, *, objective: str | None = None) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            assert project is not None
            if objective is not None:
                project.objective = objective
            await session.commit()

    asyncio.run(_update())


def _persist_acceptance(project_id: str, acceptance: object) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            project = await session.get(Project, uuid.UUID(project_id))
            assert project is not None
            project.acceptance_criteria = acceptance
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


def _corrupt_plan(plan_id: str) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            plan = await session.get(DecompositionPlan, uuid.UUID(plan_id))
            assert plan is not None and plan.plan_spec is not None
            changed = dict(plan.plan_spec)
            changed["warnings"] = ["unreviewed mutation"]
            plan.plan_spec = changed
            await session.commit()

    asyncio.run(_update())


def _change_contract(plan_id: str, contract_version: str) -> None:
    async def _update():
        async with TestSessionFactory() as session:
            plan = await session.get(DecompositionPlan, uuid.UUID(plan_id))
            assert plan is not None
            plan.contract_version = contract_version
            await session.commit()

    asyncio.run(_update())


def _plan_audits(plan_id: str) -> list[AuditEvent]:
    async def _query():
        async with TestSessionFactory() as session:
            rows = await session.execute(
                select(AuditEvent).where(AuditEvent.entity_id == uuid.UUID(plan_id))
            )
            return list(rows.scalars())

    return asyncio.run(_query())


def test_approval_materializes_exact_graph_assignments_rubrics_and_acceptance(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "owner_gate", "check": "non_empty"}]},
    )
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    response = _approve(
        client,
        headers,
        project["id"],
        plan,
        _approval_payload(plan, executor),
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan"]["status"] == "approved"
    assert body["dependency_count"] == 1
    assert [task["task_key"] for task in body["tasks"]] == ["research", "deliver"]

    tasks = client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()
    assert [task["source_plan_task_key"] for task in tasks] == ["research", "deliver"]
    assert [task["assigned_agent_id"] for task in tasks] == [executor, executor]
    assert all(task["source_plan_id"] == plan["id"] for task in tasks)
    assert all(task["acceptance_criteria"] for task in tasks)
    assert [task["max_remediations"] for task in tasks] == [1, 1]

    graph = client.get(f"/api/v1/projects/{project['id']}/graph", headers=headers).json()
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
    project_after = client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()
    keys = [criterion["key"] for criterion in project_after["acceptance_criteria"]["criteria"]]
    assert keys == ["owner_gate", "project_output"]

    approval_audits = [
        event for event in _plan_audits(plan["id"]) if event.action == "plan.approved"
    ]
    assert len(approval_audits) == 1
    assert approval_audits[0].after["plan_spec_sha256"] == plan["plan_spec_sha256"]
    assert approval_audits[0].after["dependency_count"] == 1
    assert set(approval_audits[0].after["task_policies"]) == {"research", "deliver"}
    assert all(
        policy["executor_agent_id"] == executor
        and policy["evaluator_agent_id"] is None
        and policy["max_remediations"] == 1
        and len(policy["rubric_sha256"]) == 64
        for policy in approval_audits[0].after["task_policies"].values()
    )
    assert len(approval_audits[0].after["policy_sha256"]) == 64


def test_approval_is_single_decision_and_never_duplicates_graph(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    payload = _approval_payload(plan, executor)
    assert _approve(client, headers, project["id"], plan, payload).status_code == 200

    second = _approve(client, headers, project["id"], plan, payload)
    assert second.status_code == 409
    assert len(client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()) == 2
    assert (
        len([event for event in _plan_audits(plan["id"]) if event.action == "plan.approved"]) == 1
    )


def test_hash_version_or_objective_mismatch_materializes_nothing(client):
    headers = _auth(client)
    executor = _agent(client, headers)

    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    wrong_hash = _approval_payload(plan, executor)
    wrong_hash["expected_plan_spec_sha256"] = "0" * 64
    assert _approve(client, headers, project["id"], plan, wrong_hash).status_code == 409
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    wrong_version = _approval_payload(plan, executor, expected_version=plan["version"] + 1)
    assert _approve(client, headers, project["id"], plan, wrong_version).status_code == 409
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    _mutate_project(project["id"], objective="A changed objective")
    assert (
        _approve(
            client, headers, project["id"], plan, _approval_payload(plan, executor)
        ).status_code
        == 409
    )
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    corrupt_project = _project(client, headers)
    corrupt_plan = _draft(client, headers, corrupt_project["id"])
    _corrupt_plan(corrupt_plan["id"])
    response = _approve(
        client,
        headers,
        corrupt_project["id"],
        corrupt_plan,
        _approval_payload(corrupt_plan, executor),
    )
    assert response.status_code == 409
    assert (
        client.get(f"/api/v1/projects/{corrupt_project['id']}/tasks", headers=headers).json() == []
    )

    contract_project = _project(client, headers)
    contract_plan = _draft(client, headers, contract_project["id"])
    _change_contract(contract_plan["id"], "plan_json_future")
    response = _approve(
        client,
        headers,
        contract_project["id"],
        contract_plan,
        _approval_payload(contract_plan, executor),
    )
    assert response.status_code == 409
    assert (
        client.get(f"/api/v1/projects/{contract_project['id']}/tasks", headers=headers).json() == []
    )


def test_existing_task_or_conflicting_acceptance_blocks_atomically(client):
    headers = _auth(client)
    executor = _agent(client, headers)

    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    manual = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Unreviewed manual task"},
        headers=headers,
    )
    assert manual.status_code == 201
    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, executor))
    assert response.status_code == 409
    tasks = client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()
    assert [task["title"] for task in tasks] == ["Unreviewed manual task"]

    conflict_project = _project(
        client,
        headers,
        {
            "criteria": [
                {
                    "key": "project_output",
                    "check": "contains_all",
                    "params": {"keywords": ["OWNER_ONLY"]},
                }
            ]
        },
    )
    conflict_plan = _draft(client, headers, conflict_project["id"])
    response = _approve(
        client,
        headers,
        conflict_project["id"],
        conflict_plan,
        _approval_payload(conflict_plan, executor),
    )
    assert response.status_code == 409
    assert (
        client.get(f"/api/v1/projects/{conflict_project['id']}/tasks", headers=headers).json() == []
    )


def test_identical_existing_acceptance_is_deduplicated(client):
    headers = _auth(client)
    project = _project(
        client,
        headers,
        {"criteria": [{"key": "project_output", "check": "non_empty"}]},
    )
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, executor))
    assert response.status_code == 200, response.text
    acceptance = client.get(f"/api/v1/projects/{project['id']}", headers=headers).json()[
        "acceptance_criteria"
    ]
    assert [criterion["key"] for criterion in acceptance["criteria"]] == ["project_output"]


def test_malformed_persisted_acceptance_blocks_materialization(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    _persist_acceptance(project["id"], [])

    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, executor))
    assert response.status_code == 409
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


def test_assignments_must_exactly_cover_plan_with_eligible_agents(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)

    missing = _approval_payload(plan, executor)
    missing["assignments"] = missing["assignments"][:1]
    assert _approve(client, headers, project["id"], plan, missing).status_code == 422

    duplicate = _approval_payload(plan, executor)
    duplicate["assignments"] = [duplicate["assignments"][0], duplicate["assignments"][0]]
    assert _approve(client, headers, project["id"], plan, duplicate).status_code == 422

    extra = _approval_payload(plan, executor)
    extra["assignments"].append({"task_key": "not_in_plan", "agent_id": executor})
    assert _approve(client, headers, project["id"], plan, extra).status_code == 422
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    disabled = _agent(client, headers, name="Disabled")
    _disable_agent(disabled)
    disabled_payload = _approval_payload(plan, disabled)
    assert _approve(client, headers, project["id"], plan, disabled_payload).status_code == 422

    other_headers = _auth(client)
    other_agent = _agent(client, other_headers, name="Other org")
    cross_org = _approval_payload(plan, other_agent)
    assert _approve(client, headers, project["id"], plan, cross_org).status_code == 422
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


def test_separate_evaluator_policy_is_validated_and_persisted(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    evaluator = _agent(
        client,
        headers,
        name="Evaluator",
        role="evaluator",
        capabilities=("evaluation.rubric",),
    )
    payload = _approval_payload(plan, executor)
    for assignment in payload["assignments"]:
        assignment["evaluator_agent_id"] = evaluator
        assignment["max_remediations"] = 2

    response = _approve(client, headers, project["id"], plan, payload)
    assert response.status_code == 200, response.text
    tasks = client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()
    assert all(task["evaluator_agent_id"] == evaluator for task in tasks)
    assert all(task["max_remediations"] == 2 for task in tasks)


def test_executor_must_cover_every_generated_capability(client, monkeypatch):
    class _CapabilityPlanner:
        name = "mock"

        async def run(self, request):
            plan = json.loads(MockProvider._structured_plan(request.prompt))
            plan["tasks"][0]["required_capabilities"] = ["research.web"]
            return AgentRunResult(output=json.dumps(plan), provider="mock")

    monkeypatch.setattr(decomposition_service, "get_adapter", lambda provider: _CapabilityPlanner())
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, executor))
    assert response.status_code == 422
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []

    capable = _agent(client, headers, name="Capable", capabilities=("research.web",))
    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, capable))
    assert response.status_code == 200, response.text


def test_invalid_evaluator_or_self_evaluation_blocks_approval(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)

    self_eval = _approval_payload(plan, executor)
    for assignment in self_eval["assignments"]:
        assignment["evaluator_agent_id"] = executor
    assert _approve(client, headers, project["id"], plan, self_eval).status_code == 422

    no_capability = _agent(client, headers, name="Unqualified evaluator", role="evaluator")
    invalid = _approval_payload(plan, executor)
    for assignment in invalid["assignments"]:
        assignment["evaluator_agent_id"] = no_capability
    assert _approve(client, headers, project["id"], plan, invalid).status_code == 422
    assert client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json() == []


def test_approved_plan_assignments_cannot_be_changed_by_task_endpoints(client):
    headers = _auth(client)
    project = _project(client, headers)
    plan = _draft(client, headers, project["id"])
    executor = _agent(client, headers)
    replacement = _agent(client, headers, name="Replacement")
    response = _approve(client, headers, project["id"], plan, _approval_payload(plan, executor))
    assert response.status_code == 200, response.text
    task = response.json()["tasks"][0]

    assign = client.patch(
        f"/api/v1/projects/{project['id']}/tasks/{task['task_id']}/assign",
        json={"agent_id": replacement},
        headers=headers,
    )
    assert assign.status_code == 409
    reassign = client.patch(
        f"/api/v1/projects/{project['id']}/tasks/{task['task_id']}/reassign",
        json={"agent_id": replacement},
        headers=headers,
    )
    assert reassign.status_code == 409
    persisted = client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers).json()
    assert (
        next(row for row in persisted if row["id"] == task["task_id"])["assigned_agent_id"]
        == executor
    )
