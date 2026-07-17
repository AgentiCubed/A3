"""Task execution: the engine-agnostic unit of work.

Drives a task through the execution state machine, calls the assigned agent via
its provider adapter (with a timeout), records an IMMUTABLE TaskExecution per
attempt, retries on failure, and escalates to a human (BLOCKED) when attempts are
exhausted. A worker engine (Celery now, Temporal later) simply arranges for
``execute_task`` to run; the rules live here, not in the engine.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.enums import AgentKind, RiskLevel, Verdict
from app.core.roles import ActorType
from app.models.agent import Agent
from app.models.approval import Approval
from app.models.task import Task, TaskDependency
from app.models.task_execution import TaskExecution
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import AgentRunRequest
from app.orchestration.state_machine.machine import assert_transition
from app.orchestration.state_machine.states import ExecutionState
from app.remediation.policy import RemediationContext, select_remediation
from app.services import evaluation_service, tool_runtime


class NotAssigned(Exception):
    pass


class NotExecutable(Exception):
    """The assigned agent is not an AI agent (human tasks complete out-of-band)."""


class AlreadyQueued(Exception):
    """The task is already QUEUED; re-dispatch would enqueue a duplicate message."""


@dataclass
class EvaluationConfig:
    """How to evaluate a successful execution and remediate failures."""

    rubric_specs: list[dict] = field(default_factory=list)
    evaluator_agent_id: uuid.UUID | None = None
    max_remediations: int = 1


@dataclass
class DispatchResult:
    final_state: ExecutionState
    attempts: int
    escalated: bool
    output: str | None = None
    execution_ids: list[uuid.UUID] = field(default_factory=list)
    verdict: Verdict | None = None
    remediations: int = 0


def _now() -> datetime:
    return datetime.now(UTC)


def build_prompt(task: Task, extra_context: str | None = None) -> str:
    parts = [f"Task: {task.title}"]
    if task.description:
        parts.append(task.description)
    if task.required_capabilities:
        parts.append("Required capabilities: " + ", ".join(task.required_capabilities))
    if extra_context:
        parts.append(extra_context)
    return "\n\n".join(parts)


# ── Predecessor-output handoff (WS-3) ─────────────────────────────────────
@dataclass(frozen=True)
class HandoffItem:
    """One predecessor's contribution to a successor's prompt."""

    task_id: uuid.UUID
    task_title: str
    execution_id: uuid.UUID
    output: str
    truncated: bool


async def collect_predecessor_context(session: AsyncSession, task: Task) -> list[HandoffItem]:
    """Latest successful execution output per COMPLETED predecessor.

    Outputs are consumed in dependency-creation order against a single total
    character budget (the ``handoff_budget_chars`` setting, env
    ``HANDOFF_BUDGET_CHARS``): each output is truncated to the budget
    remaining, and once the budget is exhausted later predecessors are
    dropped. Predecessors that are not COMPLETED, or completed without an
    execution output (e.g. human tasks), contribute nothing.

    Three fixed queries regardless of predecessor count: dependencies, their
    tasks, and their successful executions (latest-per-task picked in Python).
    """
    deps = (
        (
            await session.execute(
                select(TaskDependency)
                .where(TaskDependency.successor_task_id == task.id)
                .order_by(TaskDependency.created_at)
            )
        )
        .scalars()
        .all()
    )
    if not deps:
        return []
    predecessor_ids = [d.predecessor_task_id for d in deps]
    predecessors = {
        t.id: t
        for t in (await session.execute(select(Task).where(Task.id.in_(predecessor_ids))))
        .scalars()
        .all()
        if t.status == ExecutionState.COMPLETED
    }
    latest_success: dict[uuid.UUID, TaskExecution] = {}
    executions = (
        (
            await session.execute(
                select(TaskExecution)
                .where(
                    TaskExecution.task_id.in_(predecessor_ids),
                    TaskExecution.state == ExecutionState.COMPLETED,
                )
                .order_by(TaskExecution.attempt_number)
            )
        )
        .scalars()
        .all()
    )
    for execution in executions:  # ascending attempts: the last one seen wins
        latest_success[execution.task_id] = execution

    budget = get_settings().handoff_budget_chars
    items: list[HandoffItem] = []
    for dep in deps:
        if budget <= 0:
            break
        predecessor = predecessors.get(dep.predecessor_task_id)
        execution = latest_success.get(dep.predecessor_task_id)
        if predecessor is None or execution is None or not execution.output:
            continue
        truncated = len(execution.output) > budget
        output = execution.output[:budget] if truncated else execution.output
        budget -= len(output)
        items.append(
            HandoffItem(
                task_id=predecessor.id,
                task_title=predecessor.title,
                execution_id=execution.id,
                output=output,
                truncated=truncated,
            )
        )
    return items


def format_handoff(items: list[HandoffItem]) -> str | None:
    if not items:
        return None
    sections = ["Output from completed prerequisite tasks:"]
    for item in items:
        marker = " (truncated)" if item.truncated else ""
        sections.append(f"### {item.task_title}{marker}\n{item.output}")
    return "\n\n".join(sections)


def _join_context(*parts: str | None) -> str | None:
    joined = [p for p in parts if p]
    return "\n\n".join(joined) if joined else None


async def _transition(
    session: AsyncSession,
    task: Task,
    to: ExecutionState,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
    reason: str | None = None,
) -> None:
    frm = task.status
    assert_transition(frm, to)  # raises IllegalTransition
    task.status = to
    await record_audit(
        session,
        organization_id=task.organization_id,
        project_id=task.project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="task.transition",
        entity_type="Task",
        entity_id=task.id,
        before={"status": frm.value},
        after={"status": to.value, "reason": reason},
    )


async def _move_to_queued(
    session: AsyncSession, task: Task, *, actor_id: uuid.UUID | None, actor_type: ActorType
) -> None:
    """Walk legal steps to QUEUED from whatever open state the task is in."""
    if task.status == ExecutionState.PLANNED:
        await _transition(
            session, task, ExecutionState.READY, actor_id=actor_id, actor_type=actor_type
        )
    if task.status in (ExecutionState.READY, ExecutionState.FAILED, ExecutionState.BLOCKED):
        await _transition(
            session, task, ExecutionState.QUEUED, actor_id=actor_id, actor_type=actor_type
        )
    if task.status != ExecutionState.QUEUED:
        # e.g. already RUNNING/COMPLETED/CANCELLED — not dispatchable.
        assert_transition(task.status, ExecutionState.QUEUED)


async def transition_task(
    session: AsyncSession,
    task: Task,
    to: ExecutionState,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
    reason: str | None = None,
) -> None:
    """Public, audited transition used by approval handling."""
    await _transition(session, task, to, actor_id=actor_id, actor_type=actor_type, reason=reason)


async def _require_executable(session: AsyncSession, task: Task) -> Agent:
    """The task must have an assigned AI agent to be dispatchable."""
    if task.assigned_agent_id is None:
        raise NotAssigned()
    agent = await session.get(Agent, task.assigned_agent_id)
    if agent is None:
        raise NotAssigned()
    if agent.kind != AgentKind.AI:
        raise NotExecutable()
    return agent


def build_dispatch_params(
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
    max_attempts: int,
    timeout_s: float,
    evaluation: EvaluationConfig | None,
) -> dict:
    """Serialize dispatch options into the JSON-safe dict the worker accepts.

    The inverse lives in ``app.workers.tasks._parse_dispatch_params``; the two
    are covered by a round-trip test so they cannot drift apart silently.
    """
    params: dict = {
        "actor_id": str(actor_id) if actor_id else None,
        "actor_type": actor_type.value,
        "max_attempts": max_attempts,
        "timeout_s": timeout_s,
    }
    if evaluation is not None:
        params["evaluation"] = {
            "rubric_specs": evaluation.rubric_specs,
            "evaluator_agent_id": (
                str(evaluation.evaluator_agent_id) if evaluation.evaluator_agent_id else None
            ),
            "max_remediations": evaluation.max_remediations,
        }
    return params


async def queue_task(
    session: AsyncSession,
    *,
    task: Task,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> None:
    """Validate and move a task to QUEUED for asynchronous (worker) dispatch.

    Runs the same dispatchability checks as ``execute_task`` so an
    unassigned/non-AI task is rejected at the API instead of failing silently
    in the worker. A task that is *already* QUEUED is rejected here — since
    ``_move_to_queued`` treats QUEUED as a no-op, re-dispatch would otherwise
    enqueue a second worker message and run the task concurrently. (The
    worker's own re-entry through QUEUED is unaffected: it calls
    ``_move_to_queued`` directly, not this function.)
    """
    if task.status == ExecutionState.QUEUED:
        raise AlreadyQueued()
    await _require_executable(session, task)
    await _move_to_queued(session, task, actor_id=actor_id, actor_type=actor_type)


async def _create_approval(
    session: AsyncSession,
    *,
    task: Task,
    execution_id: uuid.UUID,
    requested_action: str,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> Approval:
    approval = Approval(
        organization_id=task.organization_id,
        project_id=task.project_id,
        task_execution_id=execution_id,
        requested_action=requested_action,
        risk_level=RiskLevel.MEDIUM,
    )
    session.add(approval)
    await session.flush()
    await record_audit(
        session,
        organization_id=task.organization_id,
        project_id=task.project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="approval.requested",
        entity_type="Approval",
        entity_id=approval.id,
        after={"task_id": str(task.id), "requested_action": requested_action},
    )
    return approval


async def execute_task(
    session: AsyncSession,
    *,
    task: Task,
    actor_id: uuid.UUID | None = None,
    actor_type: ActorType = ActorType.USER,
    max_attempts: int = 2,
    timeout_s: float = 30.0,
    evaluation: EvaluationConfig | None = None,
) -> DispatchResult:
    """Run a task end-to-end: execute (with retries) → evaluate → remediate.

    Without ``evaluation`` a successful run simply completes (Phase-5 behavior).
    With ``evaluation`` a successful run is graded; a failing verdict triggers the
    remediation policy, which either re-executes inline or escalates to a human.
    """
    agent = await _require_executable(session, task)

    adapter = get_adapter(agent.provider)
    credential_ref = (agent.config or {}).get("api_key_ref")
    # WS-5: the request carries schemas only for tools this agent holds a
    # grant for (adapters that support provider-native tools surface them; the
    # mock does today). Enforcement never relies on that — the runtime
    # re-checks every call against the default-deny permission table.
    tool_schemas = await tool_runtime.permitted_tool_schemas(session, agent)

    execution_ids: list[uuid.UUID] = []
    attempt = 0
    remediations = 0
    extra_context: str | None = None

    # WS-3: completed predecessors' outputs ride into every attempt's prompt;
    # what was injected is recorded on the execution row for audit.
    handoff_items = await collect_predecessor_context(session, task)
    handoff_text = format_handoff(handoff_items)
    handoff_meta = [
        {
            "task_id": str(i.task_id),
            "execution_id": str(i.execution_id),
            "chars": len(i.output),
            "truncated": i.truncated,
        }
        for i in handoff_items
    ] or None

    await _move_to_queued(session, task, actor_id=actor_id, actor_type=actor_type)

    while True:
        attempt += 1
        await _transition(
            session, task, ExecutionState.RUNNING, actor_id=actor_id, actor_type=actor_type
        )
        started = _now()
        prompt = build_prompt(task, _join_context(handoff_text, extra_context))
        request = AgentRunRequest(
            prompt=prompt, model=agent.model, credential_ref=credential_ref, tools=tool_schemas
        )
        try:
            # timeout_s is the attempt's time budget and wraps the WHOLE tool
            # loop, not just one model call (WS-5).
            result = await asyncio.wait_for(
                tool_runtime.run_with_tools(
                    session,
                    agent=agent,
                    adapter=adapter,
                    request=request,
                    task=task,
                    actor_id=actor_id,
                    actor_type=actor_type,
                ),
                timeout=timeout_s,
            )
        except TimeoutError:
            execution_ids.append(
                await _record(
                    session,
                    task=task,
                    agent=agent,
                    attempt=attempt,
                    state=ExecutionState.FAILED,
                    started=started,
                    output=None,
                    error=f"timeout after {timeout_s}s",
                    provider=agent.provider,
                    prompt_chars=len(prompt),
                    handoff=handoff_meta,
                )
            )
            outcome = await _handle_failure(
                session, task, attempt, max_attempts, actor_id=actor_id, actor_type=actor_type
            )
            if outcome is not None:
                return DispatchResult(outcome, attempt, escalated=True, execution_ids=execution_ids)
            continue
        except Exception as exc:  # noqa: BLE001 - any provider error is a failed attempt
            execution_ids.append(
                await _record(
                    session,
                    task=task,
                    agent=agent,
                    attempt=attempt,
                    state=ExecutionState.FAILED,
                    started=started,
                    output=None,
                    error=f"{type(exc).__name__}: {exc}",
                    provider=agent.provider,
                    prompt_chars=len(prompt),
                    handoff=handoff_meta,
                )
            )
            outcome = await _handle_failure(
                session, task, attempt, max_attempts, actor_id=actor_id, actor_type=actor_type
            )
            if outcome is not None:
                return DispatchResult(outcome, attempt, escalated=True, execution_ids=execution_ids)
            continue

        # Execution attempt succeeded — record it and move to evaluation.
        execution_id = await _record(
            session,
            task=task,
            agent=agent,
            attempt=attempt,
            state=ExecutionState.COMPLETED,
            started=started,
            output=result.output,
            error=None,
            provider=result.provider,
            prompt_chars=len(prompt),
            handoff=handoff_meta,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
        )
        execution_ids.append(execution_id)
        await _transition(
            session, task, ExecutionState.EVALUATING, actor_id=actor_id, actor_type=actor_type
        )

        if evaluation is None:
            await _transition(
                session, task, ExecutionState.COMPLETED, actor_id=actor_id, actor_type=actor_type
            )
            return DispatchResult(
                ExecutionState.COMPLETED,
                attempt,
                escalated=False,
                output=result.output,
                execution_ids=execution_ids,
                verdict=Verdict.PASS,
                remediations=remediations,
            )

        execution = await session.get(TaskExecution, execution_id)
        evaluator_agent = (
            await session.get(Agent, evaluation.evaluator_agent_id)
            if evaluation.evaluator_agent_id
            else None
        )
        ev = await evaluation_service.evaluate_execution(
            session,
            execution=execution,
            rubric_specs=evaluation.rubric_specs,
            evaluator_agent=evaluator_agent,
            actor_id=actor_id,
            actor_type=actor_type,
        )

        if ev.verdict == Verdict.PASS:
            await _transition(
                session, task, ExecutionState.COMPLETED, actor_id=actor_id, actor_type=actor_type
            )
            return DispatchResult(
                ExecutionState.COMPLETED,
                attempt,
                escalated=False,
                output=result.output,
                execution_ids=execution_ids,
                verdict=ev.verdict,
                remediations=remediations,
            )

        # Failed evaluation → choose and record a remediation action.
        decision = select_remediation(
            RemediationContext(
                verdict=ev.verdict,
                score=ev.score,
                gaps=list(ev.gaps or []),
                remediations_used=remediations,
                max_remediations=evaluation.max_remediations,
            )
        )
        await record_audit(
            session,
            organization_id=task.organization_id,
            project_id=task.project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action="remediation.selected",
            entity_type="TaskExecution",
            entity_id=execution_id,
            after={"action": decision.action.value, "justification": decision.justification},
        )

        if decision.auto_applicable:
            remediations += 1
            extra_context = "Address these evaluation gaps: " + "; ".join(ev.gaps or [])
            await _transition(
                session,
                task,
                ExecutionState.READY,
                actor_id=actor_id,
                actor_type=actor_type,
                reason=f"remediation: {decision.action.value}",
            )
            await _transition(
                session, task, ExecutionState.QUEUED, actor_id=actor_id, actor_type=actor_type
            )
            continue

        # Non-automatable remediation → human approval gate.
        await _create_approval(
            session,
            task=task,
            execution_id=execution_id,
            requested_action=(
                f"Evaluation failed for task '{task.title}'. Recommended remediation: "
                f"{decision.action.value} ({decision.justification})."
            ),
            actor_id=actor_id,
            actor_type=actor_type,
        )
        await _transition(
            session,
            task,
            ExecutionState.AWAITING_APPROVAL,
            actor_id=actor_id,
            actor_type=actor_type,
            reason=f"remediation: {decision.action.value}",
        )
        return DispatchResult(
            ExecutionState.AWAITING_APPROVAL,
            attempt,
            escalated=True,
            output=result.output,
            execution_ids=execution_ids,
            verdict=ev.verdict,
            remediations=remediations,
        )


async def _handle_failure(
    session: AsyncSession,
    task: Task,
    attempt: int,
    max_attempts: int,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> ExecutionState | None:
    """RUNNING -> FAILED, then either re-queue (retry) or escalate (BLOCKED).

    Returns the terminal-ish state if escalated, else None to continue retrying.
    """
    await _transition(
        session, task, ExecutionState.FAILED, actor_id=actor_id, actor_type=actor_type
    )
    if attempt < max_attempts:
        await _transition(
            session,
            task,
            ExecutionState.QUEUED,
            actor_id=actor_id,
            actor_type=actor_type,
            reason=f"retry {attempt + 1}/{max_attempts}",
        )
        return None
    # Exhausted: escalate to a human.
    await _transition(
        session,
        task,
        ExecutionState.BLOCKED,
        actor_id=actor_id,
        actor_type=actor_type,
        reason="max attempts exhausted; escalated to human",
    )
    await record_audit(
        session,
        organization_id=task.organization_id,
        project_id=task.project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="task.escalated",
        entity_type="Task",
        entity_id=task.id,
        after={"attempts": attempt},
    )
    return ExecutionState.BLOCKED


async def _record(
    session: AsyncSession,
    *,
    task: Task,
    agent: Agent,
    attempt: int,
    state: ExecutionState,
    started: datetime,
    output: str | None,
    error: str | None,
    provider: str | None,
    prompt_chars: int,
    handoff: list[dict] | None = None,
    tokens_used: int = 0,
    cost_estimate: float = 0.0,
) -> uuid.UUID:
    input_context: dict = {"prompt_chars": prompt_chars}
    if handoff:
        input_context["handoff"] = handoff
    execution = TaskExecution(
        organization_id=task.organization_id,
        task_id=task.id,
        agent_id=agent.id,
        attempt_number=attempt,
        state=state,
        input_context=input_context,
        output=output,
        error=error,
        provider=provider,
        tokens_used=tokens_used,
        cost_estimate=cost_estimate,
        started_at=started,
        finished_at=_now(),
    )
    session.add(execution)
    await session.flush()
    return execution.id


async def reassign_task(
    session: AsyncSession,
    *,
    task: Task,
    new_agent: Agent,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
) -> None:
    """Reassign a (typically failed) task to another agent, then make it ready."""
    before = str(task.assigned_agent_id)
    task.assigned_agent_id = new_agent.id
    if task.status in (ExecutionState.FAILED, ExecutionState.BLOCKED):
        await _transition(
            session,
            task,
            ExecutionState.READY,
            actor_id=actor_id,
            actor_type=actor_type,
            reason="reassigned",
        )
    await record_audit(
        session,
        organization_id=task.organization_id,
        project_id=task.project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="task.reassigned",
        entity_type="Task",
        entity_id=task.id,
        before={"agent_id": before},
        after={"agent_id": str(new_agent.id)},
    )


async def list_executions(
    session: AsyncSession, *, org_id: uuid.UUID, task_id: uuid.UUID
) -> list[TaskExecution]:
    stmt = (
        select(TaskExecution)
        .where(
            TaskExecution.organization_id == org_id,
            TaskExecution.task_id == task_id,
        )
        .order_by(TaskExecution.attempt_number)
    )
    return list((await session.execute(stmt)).scalars().all())
