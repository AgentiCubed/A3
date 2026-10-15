"""Agent tool runtime (WS-5): the loop that lets an agent actually use tools.

When ``adapter.run`` returns tool calls, this runtime — never the model —
decides what happens next, in this order for every call:

1. **Resolve**: the call's name must match a registered org Tool. Unknown → halt.
2. **Permit**: default-deny check against ``AgentToolPermission`` (expiry
   honored). No grant → halt, with a ``tool.denied`` audit event.
3. **Execute**: only against the server-side allowlist below
   (``TOOL_IMPLEMENTATIONS``); a registered-but-unimplemented tool halts. An
   implementation error is returned to the agent as a tool error, not raised.
4. **Feed back**: results are appended to the prompt under a
   ``[[TOOL_RESULTS]]`` section and the adapter is re-invoked.

Budgets bound the loop: ``TOOL_MAX_ITERATIONS`` adapter invocations and
``TOOL_MAX_CALLS`` executed calls per attempt (audited as
``tool.budget_exhausted`` when hit), while the caller's per-attempt
``timeout_s`` (applied by ``execute_task`` around the whole loop) is the time
budget. A halt surfaces as a failed execution attempt, so the normal
retry/escalation path brings a human in — a denied or runaway agent can never
grind on silently.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis import python_worker
from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.roles import ActorType
from app.models.agent import Agent, AgentToolPermission, Tool
from app.models.artifact import Artifact
from app.models.task import Task
from app.orchestration.ports import AgentAdapter, AgentRunRequest, AgentRunResult, ToolSchema
from app.services import artifact_service, tool_service

_RESULT_TEXT_MAX = 4000


class ToolDenied(Exception):
    """A tool call was refused (unknown, unpermitted, or unimplemented)."""


class ToolBudgetExceeded(Exception):
    """The tool loop hit its iteration or call budget."""


@dataclass(frozen=True)
class ToolContext:
    org_id: uuid.UUID
    project_id: uuid.UUID
    task_id: uuid.UUID
    agent_id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_type: ActorType


# ── Server-side tool implementations (the allowlist) ──────────────────────
async def _artifact_write(session: AsyncSession, ctx: ToolContext, args: dict) -> dict:
    text = args.get("content_text")
    if not isinstance(text, str) or not text:
        raise ValueError("content_text (non-empty string) is required")
    name = str(args.get("name") or "artifact.txt")
    content_type = str(args.get("content_type") or "text/plain")
    artifact = await artifact_service.store_artifact(
        session,
        artifact_service.default_store(),
        org_id=ctx.org_id,
        project_id=ctx.project_id,
        name=name,
        content_type=content_type,
        data=text.encode("utf-8"),
        produced_by_agent_id=ctx.agent_id,
        actor_id=ctx.actor_id,
        actor_type=ctx.actor_type,
    )
    return {
        "artifact_id": str(artifact.id),
        "size_bytes": artifact.size_bytes,
        "sha256": artifact.sha256,
    }


async def _artifact_read(session: AsyncSession, ctx: ToolContext, args: dict) -> dict:
    try:
        artifact_id = uuid.UUID(str(args.get("artifact_id")))
    except ValueError as exc:
        raise ValueError("artifact_id (uuid) is required") from exc
    artifact = await session.get(Artifact, artifact_id)
    if (
        artifact is None
        or artifact.organization_id != ctx.org_id
        or artifact.project_id != ctx.project_id
    ):
        # Project-scoped like the artifacts API: a task's agent cannot read
        # another project's artifacts even within its own org.
        raise ValueError("artifact not found")
    data = artifact_service.default_store().get(artifact.storage_key)
    text = data.decode("utf-8", errors="replace")
    return {
        "name": artifact.name,
        "content_type": artifact.content_type,
        "text": text[:_RESULT_TEXT_MAX],
        "truncated": len(text) > _RESULT_TEXT_MAX,
    }


async def _analysis_summary_stats(
    session: AsyncSession, ctx: ToolContext, args: dict  # noqa: ARG001
) -> dict:
    records = args.get("records")
    value_column = args.get("value_column")
    if not isinstance(records, list) or not isinstance(value_column, str):
        raise ValueError("records (list of objects) and value_column (string) are required")
    return {"stats": python_worker.summary_stats(records, value_column)}


ToolImpl = Callable[[AsyncSession, ToolContext, dict], Awaitable[dict]]

#: Registered Tool.name → server-side implementation. Registration alone does
#: NOT make a tool executable: a name absent here halts, so arbitrary execution
#: can never be introduced through the registry.
TOOL_IMPLEMENTATIONS: dict[str, ToolImpl] = {
    "artifact.write": _artifact_write,
    "artifact.read": _artifact_read,
    "analysis.summary_stats": _analysis_summary_stats,
}


# ── Permitted schemas (what the model is shown) ───────────────────────────
async def permitted_tool_schemas(session: AsyncSession, agent: Agent) -> list[ToolSchema]:
    """Schemas of tools this agent holds an unexpired grant for (one query)."""
    now = datetime.now(UTC)
    stmt = (
        select(Tool)
        .join(AgentToolPermission, AgentToolPermission.tool_id == Tool.id)
        .where(
            AgentToolPermission.agent_id == agent.id,
            Tool.organization_id == agent.organization_id,
            or_(
                AgentToolPermission.expires_at.is_(None),
                AgentToolPermission.expires_at > now,
            ),
        )
    )
    tools = (await session.execute(stmt)).scalars().all()
    return [
        ToolSchema(name=tool.name, description=tool.description, input_schema=tool.schema or {})
        for tool in tools
    ]


# ── The runtime loop ──────────────────────────────────────────────────────
async def run_with_tools(
    session: AsyncSession,
    *,
    agent: Agent,
    adapter: AgentAdapter,
    request: AgentRunRequest,
    task: Task,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> AgentRunResult:
    """Run the adapter, executing permitted tool calls until a final answer.

    Returns the final (tool-free) AgentRunResult. Raises ToolDenied or
    ToolBudgetExceeded to halt the attempt; both are audited first.
    """
    settings = get_settings()
    ctx = ToolContext(
        org_id=task.organization_id,
        project_id=task.project_id,
        task_id=task.id,
        agent_id=agent.id,
        actor_id=actor_id,
        actor_type=actor_type,
    )
    calls_executed = 0
    current = request
    for iteration in range(1, settings.tool_max_iterations + 1):
        result = await adapter.run(current)
        if not result.tool_calls:
            return result
        if iteration == settings.tool_max_iterations:
            await _audit(session, ctx, "tool.budget_exhausted", {"iterations": iteration})
            raise ToolBudgetExceeded(
                f"tool loop needs more than {settings.tool_max_iterations} model invocations"
            )
        events: list[dict] = []
        for call in result.tool_calls:
            if calls_executed >= settings.tool_max_calls:
                await _audit(session, ctx, "tool.budget_exhausted", {"calls": calls_executed})
                raise ToolBudgetExceeded(f"tool loop exceeded {settings.tool_max_calls} tool calls")
            calls_executed += 1
            events.append(await _execute_call(session, ctx, agent, call.name, call.arguments))
        current = replace(
            current,
            prompt=(
                current.prompt
                + "\n\n[[TOOL_RESULTS]]\n"
                + json.dumps(events, default=str)
                + "\nUse these tool results to produce your final answer."
            ),
        )
    raise AssertionError("unreachable")  # pragma: no cover


async def _execute_call(
    session: AsyncSession,
    ctx: ToolContext,
    agent: Agent,
    name: str,
    arguments: dict[str, Any],
) -> dict:
    tool = (
        (
            await session.execute(
                select(Tool).where(Tool.organization_id == ctx.org_id, Tool.name == name)
            )
        )
        .scalars()
        .first()
    )
    if tool is None:
        await _audit(session, ctx, "tool.denied", {"tool": name, "reason": "unknown tool"})
        raise ToolDenied(f"unknown tool: {name}")
    if not await tool_service.has_permission(
        session, agent_id=agent.id, tool_id=tool.id, now=datetime.now(UTC)
    ):
        await _audit(session, ctx, "tool.denied", {"tool": name, "reason": "no permission"})
        raise ToolDenied(f"agent has no permission for tool: {name}")
    impl = TOOL_IMPLEMENTATIONS.get(tool.name)
    if impl is None:
        await _audit(
            session, ctx, "tool.denied", {"tool": name, "reason": "no server-side implementation"}
        )
        raise ToolDenied(f"tool has no server-side implementation: {name}")

    try:
        output = await impl(session, ctx, arguments or {})
        status = "ok"
        event: dict = {"tool": name, "status": status, "result": output}
    except Exception as exc:  # noqa: BLE001 - reported to the agent, loop continues
        status = "error"
        event = {"tool": name, "status": status, "error": f"{type(exc).__name__}: {exc}"}
    await _audit(session, ctx, "tool.invoked", {"tool": name, "status": status})
    return event


async def _audit(session: AsyncSession, ctx: ToolContext, action: str, extra: dict) -> None:
    await record_audit(
        session,
        organization_id=ctx.org_id,
        project_id=ctx.project_id,
        actor_type=ctx.actor_type,
        actor_id=ctx.actor_id,
        action=action,
        entity_type="Tool",
        after={"task_id": str(ctx.task_id), "agent_id": str(ctx.agent_id), **extra},
    )
