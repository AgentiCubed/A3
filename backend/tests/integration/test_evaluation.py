"""Evaluation, executor/evaluator separation, closed-loop remediation, approvals."""

from __future__ import annotations

import uuid

import pytest

from app.db.base import ImmutableError
from app.models.evaluation import Evaluation


def _auth(client) -> dict[str, str]:
    email = f"ev-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _setup(client, headers):
    pid = client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": "Write brief"}, headers=headers
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents", json={"name": "Exec", "kind": "ai", "provider": "mock"}, headers=headers
    ).json()["id"]
    client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    return pid, task_id, agent_id


_PASS_RUBRIC = [{"key": "nonempty", "check": "non_empty", "weight": 1}]
_FAIL_RUBRIC = [
    {
        "key": "kw",
        "check": "contains_all",
        "weight": 1,
        "params": {"keywords": ["ABSENT_TOKEN_XYZ"]},
    }
]


def test_dispatch_with_passing_rubric_completes(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _PASS_RUBRIC},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["final_state"] == "completed"
    assert body["verdict"] == "pass"

    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert len(evals) == 1
    assert evals[0]["verdict"] == "pass"
    assert evals[0]["evaluator_kind"] == "deterministic"


def test_failed_eval_escalates_and_creates_approval(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _FAIL_RUBRIC, "max_remediations": 0},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_state"] == "awaiting_approval"
    assert body["escalated"]
    assert body["verdict"] == "fail"

    approvals = client.get(f"/api/v1/projects/{pid}/approvals", headers=headers).json()
    assert len(approvals) == 1
    assert approvals[0]["status"] == "pending"


def test_remediation_reexecutes_then_escalates(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _FAIL_RUBRIC, "max_remediations": 1},
        headers=headers,
    )
    body = resp.json()
    assert body["remediations"] == 1
    assert body["final_state"] == "awaiting_approval"
    # One auto remediation => two execution attempts => two evaluations.
    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert len(evals) == 2


def test_executor_cannot_evaluate_itself(client):
    headers = _auth(client)
    pid, task_id, agent_id = _setup(client, headers)
    # evaluator == executor → rejected (executor/evaluator separation).
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _PASS_RUBRIC, "evaluator_agent_id": agent_id},
        headers=headers,
    )
    assert resp.status_code == 422


def test_separate_evaluator_agent_records_agent_kind(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    evaluator = client.post(
        "/api/v1/agents",
        json={"name": "Judge", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _PASS_RUBRIC, "evaluator_agent_id": evaluator},
        headers=headers,
    )
    assert resp.status_code == 200
    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert evals[0]["evaluator_kind"] == "agent"
    assert evals[0]["evaluator_agent_id"] == evaluator


def test_approval_approve_completes_task(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _FAIL_RUBRIC, "max_remediations": 0},
        headers=headers,
    )
    approval_id = client.get(f"/api/v1/projects/{pid}/approvals", headers=headers).json()[0]["id"]

    decide = client.post(
        f"/api/v1/projects/{pid}/approvals/{approval_id}/decide",
        json={"approve": True, "comment": "looks fine"},
        headers=headers,
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "approved"

    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "completed"


def test_approval_reject_routes_to_ready(client):
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _FAIL_RUBRIC, "max_remediations": 0},
        headers=headers,
    )
    approval_id = client.get(f"/api/v1/projects/{pid}/approvals", headers=headers).json()[0]["id"]
    client.post(
        f"/api/v1/projects/{pid}/approvals/{approval_id}/decide",
        json={"approve": False},
        headers=headers,
    )
    tasks = client.get(f"/api/v1/projects/{pid}/tasks", headers=headers).json()
    assert next(t for t in tasks if t["id"] == task_id)["status"] == "ready"


async def test_evaluation_is_immutable(session):
    ev = Evaluation(
        organization_id=uuid.uuid4(),
        task_execution_id=uuid.uuid4(),
        evaluator_kind="deterministic",
        verdict="pass",
        score=1.0,
        summary="ok",
    )
    session.add(ev)
    await session.commit()
    ev.summary = "tampered"
    with pytest.raises(ImmutableError):
        await session.commit()


# ── WS-4: structured evaluator verdict contract, fail-closed ──────────────
class _ScriptedEvaluator:
    """Evaluator adapter double returning a fixed response (or raising)."""

    name = "mock"

    def __init__(self, response: str | None = None, error: bool = False) -> None:
        self.response = response
        self.error = error

    async def run(self, request):
        from app.orchestration.ports import AgentRunResult

        if self.error:
            raise RuntimeError("judge unreachable")
        return AgentRunResult(output=self.response or "", provider="mock")


def _evaluator(client, headers) -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": "Judge", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]


def test_malformed_evaluator_response_fails_closed(client, monkeypatch):
    """A prose (contract-violating) judge can never silently PASS work."""

    class _MarkedExecutor:
        name = "mock"

        async def run(self, request):
            from app.orchestration.ports import AgentRunResult

            return AgentRunResult(
                output="[[MALFORMED]] a long and otherwise plausible work product",
                provider="mock",
            )

    from app.services import execution_service

    # Executor produces output that trips the mock judge into prose; the real
    # MockProvider evaluator and the real parser handle the rest.
    monkeypatch.setattr(execution_service, "get_adapter", lambda name: _MarkedExecutor())

    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={
            "rubric": _PASS_RUBRIC,
            "evaluator_agent_id": _evaluator(client, headers),
            "max_remediations": 0,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verdict"] == "needs_revision"  # fail-closed, NOT pass
    assert body["final_state"] == "awaiting_approval"

    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert evals[0]["verdict"] == "needs_revision"
    assert "[failed closed]" in evals[0]["summary"]


def test_evaluator_agent_error_fails_closed(client, monkeypatch):
    """An unreachable judge gates for human review instead of silently passing."""
    from app.services import evaluation_service

    monkeypatch.setattr(
        evaluation_service, "get_adapter", lambda name: _ScriptedEvaluator(error=True)
    )

    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={
            "rubric": _PASS_RUBRIC,
            "evaluator_agent_id": _evaluator(client, headers),
            "max_remediations": 0,
        },
        headers=headers,
    )
    body = resp.json()
    assert body["verdict"] == "needs_revision"
    assert body["final_state"] == "awaiting_approval"


def test_agent_json_fail_verdict_gates_despite_passing_rubric(client, monkeypatch):
    """A well-formed FAIL from the judge downgrades a deterministic PASS."""
    from app.services import evaluation_service

    monkeypatch.setattr(
        evaluation_service,
        "get_adapter",
        lambda name: _ScriptedEvaluator(
            '{"verdict": "fail", "score": 0.1, "critique": "wrong approach", '
            '"gaps": ["missing requirement X"]}'
        ),
    )

    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={
            "rubric": _PASS_RUBRIC,
            "evaluator_agent_id": _evaluator(client, headers),
            "max_remediations": 0,
        },
        headers=headers,
    )
    body = resp.json()
    assert body["verdict"] == "fail"
    assert body["final_state"] == "awaiting_approval"

    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert "missing requirement X" in (evals[0]["gaps"] or [])


def test_wellformed_mock_evaluator_pass_completes(client):
    """End-to-end through the real mock judge: valid JSON verdict, PASS, done."""
    headers = _auth(client)
    pid, task_id, _ = _setup(client, headers)
    resp = client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch",
        json={"rubric": _PASS_RUBRIC, "evaluator_agent_id": _evaluator(client, headers)},
        headers=headers,
    )
    body = resp.json()
    assert body["final_state"] == "completed"
    assert body["verdict"] == "pass"

    evals = client.get(
        f"/api/v1/projects/{pid}/tasks/{task_id}/evaluations", headers=headers
    ).json()
    assert evals[0]["evaluator_kind"] == "agent"
    assert evals[0]["verdict"] == "pass"
    assert "[failed closed]" not in evals[0]["summary"]
