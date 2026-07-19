"""WS-5 agent tool runtime: permitted round-trips, default-deny halts, budgets.

Proves the remediation-plan WS-5 definition of done, hermetically, using the
MockProvider's tool markers: a permitted tool call round-trips into a real
artifact, a denied/unknown/unimplemented call halts the attempt with a
``tool.denied`` audit event, and budgets terminate a runaway loop.
"""

from __future__ import annotations

import asyncio
import json
import uuid

from sqlalchemy import select

from app.core.config import get_settings
from app.models.audit_event import AuditEvent
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"tr-{uuid.uuid4().hex[:10]}@example.com"
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


def _task(client, headers, pid, title, description="") -> str:
    return client.post(
        f"/api/v1/projects/{pid}/tasks",
        json={"title": title, "description": description},
        headers=headers,
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


def _register_tool(client, headers, name, kind="python_fn") -> str:
    resp = client.post(
        "/api/v1/tools",
        json={"name": name, "kind": kind, "description": f"{name} tool"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _grant(client, headers, agent_id, tool_id) -> None:
    resp = client.post(
        f"/api/v1/agents/{agent_id}/tools/{tool_id}/permission", json={}, headers=headers
    )
    assert resp.status_code == 201, resp.text


def _dispatch(client, headers, pid, task_id, **body):
    return client.post(
        f"/api/v1/projects/{pid}/tasks/{task_id}/dispatch", json=body, headers=headers
    )


def _artifacts(client, headers, pid) -> list[dict]:
    return client.get(f"/api/v1/projects/{pid}/artifacts", headers=headers).json()


def _executions(client, headers, pid, task_id) -> list[dict]:
    return client.get(f"/api/v1/projects/{pid}/tasks/{task_id}/executions", headers=headers).json()


def _audits_for_task(task_id: str, action: str) -> list[dict]:
    """Audit rows of one action referencing this task (queried off-request)."""

    async def _query():
        async with TestSessionFactory() as session:
            rows = (
                (await session.execute(select(AuditEvent).where(AuditEvent.action == action)))
                .scalars()
                .all()
            )
            return [r.after for r in rows if (r.after or {}).get("task_id") == task_id]

    return asyncio.run(_query())


def _marker(tool: str, **args) -> str:
    return f"[[TOOL:{tool}:{json.dumps(args)}]]"


def test_permitted_tool_round_trip_creates_artifact(client, monkeypatch, tmp_path):
    """The WS-5 acceptance test: call tool -> artifact exists -> final answer."""
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    tool_id = _register_tool(client, headers, "artifact.write")
    _grant(client, headers, agent_id, tool_id)

    task_id = _task(
        client,
        headers,
        pid,
        "Write notes",
        "Save the notes. " + _marker("artifact.write", name="notes.txt", content_text="hello"),
    )
    _assign(client, headers, pid, task_id, agent_id)

    resp = _dispatch(client, headers, pid, task_id)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["final_state"] == "completed"
    assert body["output"]  # the post-tool final answer, not an empty tool turn

    arts = _artifacts(client, headers, pid)
    assert len(arts) == 1
    assert arts[0]["name"] == "notes.txt"
    assert arts[0]["produced_by_agent_id"] == agent_id

    invoked = _audits_for_task(task_id, "tool.invoked")
    assert [a["status"] for a in invoked] == ["ok"]
    assert invoked[0]["tool"] == "artifact.write"


def test_artifact_read_round_trip(client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    write_id = _register_tool(client, headers, "artifact.write")
    read_id = _register_tool(client, headers, "artifact.read")
    _grant(client, headers, agent_id, write_id)
    _grant(client, headers, agent_id, read_id)

    t1 = _task(
        client,
        headers,
        pid,
        "Write",
        _marker("artifact.write", name="report.md", content_text="quarterly numbers"),
    )
    _assign(client, headers, pid, t1, agent_id)
    assert _dispatch(client, headers, pid, t1).json()["final_state"] == "completed"
    artifact_id = _artifacts(client, headers, pid)[0]["id"]

    t2 = _task(client, headers, pid, "Read", _marker("artifact.read", artifact_id=artifact_id))
    _assign(client, headers, pid, t2, agent_id)
    assert _dispatch(client, headers, pid, t2).json()["final_state"] == "completed"
    assert _audits_for_task(t2, "tool.invoked")[0]["status"] == "ok"


def test_denied_tool_halts_attempt_with_audit(client, monkeypatch, tmp_path):
    """Registered but ungranted: default-deny halts, audits, creates nothing."""
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    _register_tool(client, headers, "artifact.write")  # no grant

    task_id = _task(client, headers, pid, "Sneaky", _marker("artifact.write", content_text="nope"))
    _assign(client, headers, pid, task_id, agent_id)

    resp = _dispatch(client, headers, pid, task_id, max_attempts=1)
    assert resp.status_code == 200
    body = resp.json()
    assert body["final_state"] == "blocked"  # halted attempt -> escalated to human
    assert body["escalated"] is True

    execs = _executions(client, headers, pid, task_id)
    assert "no permission for tool" in execs[0]["error"]

    denied = _audits_for_task(task_id, "tool.denied")
    assert len(denied) == 1
    assert denied[0]["reason"] == "no permission"
    assert _artifacts(client, headers, pid) == []
    assert _audits_for_task(task_id, "tool.invoked") == []


def test_unknown_tool_halts_with_audit(client):
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)

    task_id = _task(client, headers, pid, "Ghost", _marker("artifact.write", content_text="x"))
    _assign(client, headers, pid, task_id, agent_id)

    body = _dispatch(client, headers, pid, task_id, max_attempts=1).json()
    assert body["final_state"] == "blocked"
    assert _audits_for_task(task_id, "tool.denied")[0]["reason"] == "unknown tool"


def test_registered_but_unimplemented_tool_halts(client):
    """Registry rows alone cannot introduce execution: no allowlist entry, no run."""
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    tool_id = _register_tool(client, headers, "shell.exec", kind="shell")
    _grant(client, headers, agent_id, tool_id)

    task_id = _task(client, headers, pid, "Shell", _marker("shell.exec", cmd="rm -rf /"))
    _assign(client, headers, pid, task_id, agent_id)

    body = _dispatch(client, headers, pid, task_id, max_attempts=1).json()
    assert body["final_state"] == "blocked"
    assert _audits_for_task(task_id, "tool.denied")[0]["reason"] == "no server-side implementation"


def test_runaway_tool_loop_terminated_by_iteration_budget(client, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    monkeypatch.setattr(get_settings(), "tool_max_iterations", 2)
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    tool_id = _register_tool(client, headers, "artifact.write")
    _grant(client, headers, agent_id, tool_id)

    task_id = _task(client, headers, pid, "Runaway", "[[TOOL_LOOP:artifact.write]]")
    _assign(client, headers, pid, task_id, agent_id)

    body = _dispatch(client, headers, pid, task_id, max_attempts=1).json()
    assert body["final_state"] == "blocked"  # terminated, not spinning
    execs = _executions(client, headers, pid, task_id)
    assert "ToolBudgetExceeded" in execs[0]["error"]
    assert len(_audits_for_task(task_id, "tool.budget_exhausted")) == 1


def test_analysis_tool_round_trip(client):
    headers = _auth(client)
    pid = _project(client, headers)
    agent_id = _agent(client, headers)
    tool_id = _register_tool(client, headers, "analysis.summary_stats")
    _grant(client, headers, agent_id, tool_id)

    task_id = _task(
        client,
        headers,
        pid,
        "Stats",
        _marker(
            "analysis.summary_stats",
            records=[{"g": "a", "v": 1}, {"g": "b", "v": 3}],
            value_column="v",
        ),
    )
    _assign(client, headers, pid, task_id, agent_id)

    body = _dispatch(client, headers, pid, task_id).json()
    assert body["final_state"] == "completed"
    assert _audits_for_task(task_id, "tool.invoked")[0]["status"] == "ok"


def test_artifact_read_is_project_scoped(client, monkeypatch, tmp_path):
    """An agent cannot read another project's artifact, even in its own org."""
    monkeypatch.setattr(get_settings(), "artifact_store_path", str(tmp_path))
    headers = _auth(client)
    pid_a = _project(client, headers)
    pid_b = _project(client, headers)
    agent_id = _agent(client, headers)
    write_id = _register_tool(client, headers, "artifact.write")
    read_id = _register_tool(client, headers, "artifact.read")
    _grant(client, headers, agent_id, write_id)
    _grant(client, headers, agent_id, read_id)

    # Write an artifact in project A.
    t1 = _task(client, headers, pid_a, "Write", _marker("artifact.write", content_text="secret"))
    _assign(client, headers, pid_a, t1, agent_id)
    assert _dispatch(client, headers, pid_a, t1).json()["final_state"] == "completed"
    foreign_artifact = _artifacts(client, headers, pid_a)[0]["id"]

    # A task in project B tries to read it: the tool errors, it is not served.
    marker = _marker("artifact.read", artifact_id=foreign_artifact)
    t2 = _task(client, headers, pid_b, "Read", marker)
    _assign(client, headers, pid_b, t2, agent_id)
    assert _dispatch(client, headers, pid_b, t2).json()["final_state"] == "completed"
    invoked = _audits_for_task(t2, "tool.invoked")
    assert invoked[0]["status"] == "error"
