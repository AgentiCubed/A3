"""WS-3 predecessor-output handoff: completed prerequisites feed successor prompts.

Proves the remediation-plan WS-3 definition of done, hermetically: after A
completes, dispatching B injects A's execution output into B's prompt through
the extra-context socket, and the injection is recorded in ``input_context``
on B's execution row (visible via the executions API).
"""

from __future__ import annotations

import uuid

from app.core.config import get_settings
from app.orchestration.ports import AgentRunRequest, AgentRunResult
from app.services import execution_service


def _auth(client) -> dict[str, str]:
    email = f"ho-{uuid.uuid4().hex[:10]}@example.com"
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


def _task(client, headers, pid, title) -> str:
    return client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": title}, headers=headers
    ).json()["id"]


def _agent(client, headers, name="Worker") -> str:
    return client.post(
        "/api/v1/agents",
        json={"name": name, "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]


def _assign(client, headers, pid, task_id, agent_id) -> None:
    resp = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


def _depend(client, headers, pid, predecessor, successor) -> None:
    resp = client.post(
        f"/api/v1/projects/{pid}/dependencies",
        json={"predecessor_task_id": predecessor, "successor_task_id": successor},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


def _dispatch(client, headers, pid, task_id, **body):
    return client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json=body, headers=headers
    )


def _executions(client, headers, pid, task_id) -> list[dict]:
    return client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()


class _EchoAdapter:
    """Adapter double: records every prompt; output names the task it ran.

    The task title is the first prompt line (``Task: <title>``), so the output
    ``OUTPUT::<title>::<n>`` is a unique, searchable marker for handoff
    assertions. ``fail_first_for`` makes attempt 1 for those titles raise, to
    exercise "latest *successful* execution" selection.
    """

    name = "mock"

    def __init__(self, output_size: int = 0, fail_first_for: set[str] | None = None) -> None:
        self.prompts: list[str] = []
        self.output_size = output_size
        self.fail_first_for = fail_first_for or set()
        self._attempts: dict[str, int] = {}

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        self.prompts.append(request.prompt)
        title = request.prompt.splitlines()[0].removeprefix("Task: ")
        self._attempts[title] = self._attempts.get(title, 0) + 1
        if title in self.fail_first_for and self._attempts[title] == 1:
            raise RuntimeError("scripted first-attempt failure")
        output = f"OUTPUT::{title}::{self._attempts[title]}"
        if self.output_size:
            output = output.ljust(self.output_size, "x")
        return AgentRunResult(output=output, provider="mock")


def _install(monkeypatch, adapter) -> None:
    monkeypatch.setattr(execution_service, "get_adapter", lambda name: adapter)


def test_predecessor_output_lands_in_successor_prompt_and_is_recorded(client, monkeypatch):
    """The WS-3 acceptance test."""
    adapter = _EchoAdapter()
    _install(monkeypatch, adapter)

    headers = _auth(client)
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    _assign(client, headers, pid, a, agent)
    _assign(client, headers, pid, b, agent)
    _depend(client, headers, pid, a, b)

    assert _dispatch(client, headers, pid, a).json()["final_state"] == "completed"
    # A ran with no handoff: nothing was completed before it.
    assert "prerequisite" not in adapter.prompts[0]
    a_execs = _executions(client, headers, pid, a)
    assert "handoff" not in a_execs[0]["input_context"]

    assert _dispatch(client, headers, pid, b).json()["final_state"] == "completed"

    # B's prompt contains A's exact output, under the handoff header.
    b_prompt = adapter.prompts[1]
    assert "Output from completed prerequisite tasks:" in b_prompt
    assert "### A\nOUTPUT::A::1" in b_prompt

    # The injection is recorded on B's execution row.
    b_execs = _executions(client, headers, pid, b)
    assert len(b_execs) == 1
    handoff = b_execs[0]["input_context"]["handoff"]
    assert handoff == [
        {
            "task_id": a,
            "execution_id": a_execs[0]["id"],
            "chars": len("OUTPUT::A::1"),
            "truncated": False,
        }
    ]
    assert b_execs[0]["input_context"]["prompt_chars"] == len(b_prompt)


def test_handoff_truncates_to_budget(client, monkeypatch):
    adapter = _EchoAdapter(output_size=500)
    _install(monkeypatch, adapter)
    monkeypatch.setattr(get_settings(), "handoff_budget_chars", 100)

    headers = _auth(client)
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    _assign(client, headers, pid, a, agent)
    _assign(client, headers, pid, b, agent)
    _depend(client, headers, pid, a, b)

    _dispatch(client, headers, pid, a)
    a_output = _executions(client, headers, pid, a)[0]["output"]
    _dispatch(client, headers, pid, b)

    assert "### A (truncated)\n" + a_output[:100] in adapter.prompts[1]
    assert a_output[:101] not in adapter.prompts[1]
    handoff = _executions(client, headers, pid, b)[0]["input_context"]["handoff"]
    assert handoff[0]["chars"] == 100
    assert handoff[0]["truncated"] is True


def test_multiple_predecessors_share_one_budget_in_order(client, monkeypatch):
    adapter = _EchoAdapter(output_size=80)
    _install(monkeypatch, adapter)
    monkeypatch.setattr(get_settings(), "handoff_budget_chars", 100)

    headers = _auth(client)
    pid = _project(client, headers)
    a1 = _task(client, headers, pid, "A1")
    a2 = _task(client, headers, pid, "A2")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    for t in (a1, a2, b):
        _assign(client, headers, pid, t, agent)
    _depend(client, headers, pid, a1, b)
    _depend(client, headers, pid, a2, b)

    _dispatch(client, headers, pid, a1)
    _dispatch(client, headers, pid, a2)
    _dispatch(client, headers, pid, b)

    handoff = _executions(client, headers, pid, b)[0]["input_context"]["handoff"]
    assert [h["task_id"] for h in handoff] == [a1, a2]
    # A1 fits whole (80 chars); A2 gets the remaining 20 and is truncated.
    assert handoff[0]["chars"] == 80
    assert handoff[0]["truncated"] is False
    assert handoff[1]["chars"] == 20
    assert handoff[1]["truncated"] is True
    assert "### A1\n" in adapter.prompts[2]
    assert "### A2 (truncated)\n" in adapter.prompts[2]


def test_incomplete_predecessor_contributes_nothing(client, monkeypatch):
    """Direct dispatch of B while A never ran: no handoff, no crash."""
    adapter = _EchoAdapter()
    _install(monkeypatch, adapter)

    headers = _auth(client)
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    _assign(client, headers, pid, a, agent)
    _assign(client, headers, pid, b, agent)
    _depend(client, headers, pid, a, b)

    assert _dispatch(client, headers, pid, b).json()["final_state"] == "completed"
    assert "prerequisite" not in adapter.prompts[0]
    assert "handoff" not in _executions(client, headers, pid, b)[0]["input_context"]


def test_handoff_uses_latest_successful_execution(client, monkeypatch):
    """A predecessor whose first attempt failed hands off the retry's output."""
    adapter = _EchoAdapter(fail_first_for={"A"})
    _install(monkeypatch, adapter)

    headers = _auth(client)
    pid = _project(client, headers)
    a = _task(client, headers, pid, "A")
    b = _task(client, headers, pid, "B")
    agent = _agent(client, headers)
    _assign(client, headers, pid, a, agent)
    _assign(client, headers, pid, b, agent)
    _depend(client, headers, pid, a, b)

    result = _dispatch(client, headers, pid, a, max_attempts=2).json()
    assert result["final_state"] == "completed"
    assert result["attempts"] == 2

    _dispatch(client, headers, pid, b)
    assert "### A\nOUTPUT::A::2" in adapter.prompts[-1]
    a_execs = _executions(client, headers, pid, a)
    completed = next(e for e in a_execs if e["state"] == "completed")
    handoff = _executions(client, headers, pid, b)[0]["input_context"]["handoff"]
    assert handoff[0]["execution_id"] == completed["id"]
