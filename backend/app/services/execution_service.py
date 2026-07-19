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

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.audit import record_audit
from app.core.config import get_settings
from app.core.enums import AgentKind, AgentRole, AgentStatus, ProjectStatus, RiskLevel, Verdict
from app.core.roles import ActorType
from app.evaluation.specs import RubricSpecError, merge_rubric_specs, rubric_sha256
from app.models.agent import Agent, AgentCapability
from app.models.approval import Approval
from app.models.project import Project
from app.models.task import Task, TaskDependency
from app.models.task_execution import TaskExecution
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import AgentRunRequest
from app.orchestration.state_machine.machine import IllegalTransition, assert_transition
from app.orchestration.state_machine.states import ExecutionState
from app.remediation.policy import RemediationContext, select_remediation
from app.services import (
    evaluation_service,
    governed_evidence_service,
    project_lock_service,
    tool_runtime,
)


class NotAssigned(Exception):
    pass


class NotExecutable(Exception):
    """The assigned agent is not currently eligible to execute this task."""


class AlreadyQueued(IllegalTransition):
    """A competing dispatcher already claimed this task.

    This remains an ``IllegalTransition`` so the existing inline API path maps
    a lost claim to HTTP 409, while the asynchronous path can continue to catch
    the more specific exception before submitting a duplicate worker message.
    """

    def __init__(self) -> None:
        self.frm = ExecutionState.QUEUED
        self.to = ExecutionState.RUNNING
        Exception.__init__(self, "task dispatch was already claimed by another transaction")


class EvaluationConfigConflict(Exception):
    """A request tried to weaken or conflict with persisted evaluation policy."""


class GovernedAssignmentLocked(Exception):
    """A materialized plan assignment cannot be changed outside plan governance."""


class GovernedProjectNotActive(Exception):
    """Plan-derived tasks cannot execute before the governed project starts."""


class GovernedDependenciesIncomplete(Exception):
    """A plan-derived task cannot bypass its approved predecessor gates."""


@dataclass
class EvaluationConfig:
    """Optional request overlay for evaluating and remediating an execution."""

    rubric_specs: list[dict] = field(default_factory=list)
    evaluator_agent_id: uuid.UUID | None = None
    max_remediations: int | None = None


@dataclass(frozen=True)
class ResolvedEvaluationConfig:
    """Authoritative policy resolved from the Task plus an additive request overlay."""

    rubric_specs: list[dict]
    rubric_sha256: str
    evaluator_agent_id: uuid.UUID | None
    max_remediations: int
    sources: list[str]


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


async def _compare_and_transition_governed(
    session: AsyncSession,
    task: Task,
    expected: ExecutionState,
    to: ExecutionState,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
    reason: str | None = None,
) -> None:
    """Atomically claim one governed transition and audit the winner.

    A normal ORM assignment is a read-then-write operation: two sessions can
    both read QUEUED and both begin provider execution. The conditional UPDATE
    makes the persisted state the arbiter. On PostgreSQL a competing UPDATE
    waits for the winner and then re-checks the predicate; exactly one caller
    can change ``expected`` to ``to``. The task instance is synchronized as a
    committed value so a later flush cannot emit a stale unconditional write.
    """
    if task.source_plan_id is None:
        raise ValueError("atomic governed transition requires plan provenance")
    assert_transition(expected, to)
    result = await session.execute(
        update(Task)
        .where(
            Task.id == task.id,
            Task.organization_id == task.organization_id,
            Task.source_plan_id == task.source_plan_id,
            Task.status == expected,
        )
        .values(status=to)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        await session.refresh(task)
        raise AlreadyQueued()
    set_committed_value(task, "status", to)
    await record_audit(
        session,
        organization_id=task.organization_id,
        project_id=task.project_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="task.transition",
        entity_type="Task",
        entity_id=task.id,
        before={"status": expected.value},
        after={"status": to.value, "reason": reason},
    )


async def _move_governed_to_queued(
    session: AsyncSession,
    task: Task,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> None:
    """Walk a governed task to QUEUED using conditional state claims."""
    if task.status == ExecutionState.PLANNED:
        await _compare_and_transition_governed(
            session,
            task,
            ExecutionState.PLANNED,
            ExecutionState.READY,
            actor_id=actor_id,
            actor_type=actor_type,
        )
    if task.status in (ExecutionState.READY, ExecutionState.FAILED, ExecutionState.BLOCKED):
        expected = task.status
        await _compare_and_transition_governed(
            session,
            task,
            expected,
            ExecutionState.QUEUED,
            actor_id=actor_id,
            actor_type=actor_type,
        )
    if task.status != ExecutionState.QUEUED:
        assert_transition(task.status, ExecutionState.QUEUED)


async def _claim_governed_execution(
    session: AsyncSession,
    task: Task,
    *,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> None:
    """Atomically claim the first RUNNING transition before provider work."""
    await _move_governed_to_queued(
        session,
        task,
        actor_id=actor_id,
        actor_type=actor_type,
    )
    await _compare_and_transition_governed(
        session,
        task,
        ExecutionState.QUEUED,
        ExecutionState.RUNNING,
        actor_id=actor_id,
        actor_type=actor_type,
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
    """Revalidate the assigned executor at the moment work is dispatched."""
    if task.assigned_agent_id is None:
        raise NotAssigned()
    agent = await session.get(Agent, task.assigned_agent_id)
    if agent is None:
        raise NotAssigned()
    if (
        agent.organization_id != task.organization_id
        or agent.kind != AgentKind.AI
        or agent.status != AgentStatus.ACTIVE
        or agent.default_role not in {AgentRole.EXECUTOR, AgentRole.EITHER}
        or not agent.provider
    ):
        raise NotExecutable()
    required = set(task.required_capabilities or [])
    if required:
        held = set(
            (
                await session.execute(
                    select(AgentCapability.capability).where(
                        AgentCapability.organization_id == task.organization_id,
                        AgentCapability.agent_id == agent.id,
                    )
                )
            )
            .scalars()
            .all()
        )
        if not required <= held:
            raise NotExecutable()
    return agent


async def _require_active_governed_project(session: AsyncSession, task: Task) -> None:
    """Prevent every dispatch path from bypassing the one governed start gate."""
    if task.source_plan_id is None:
        return
    project = await session.get(Project, task.project_id)
    if (
        project is None
        or project.organization_id != task.organization_id
        or project.status != ProjectStatus.ACTIVE
    ):
        raise GovernedProjectNotActive()


async def _require_governed_dependencies_complete(session: AsyncSession, task: Task) -> None:
    """Apply dependency ordering centrally, including individual dispatch calls."""
    if task.source_plan_id is None:
        return
    predecessors = (
        (
            await session.execute(
                select(Task)
                .join(
                    TaskDependency,
                    TaskDependency.predecessor_task_id == Task.id,
                )
                .where(TaskDependency.successor_task_id == task.id)
            )
        )
        .scalars()
        .all()
    )
    if any(predecessor.status != ExecutionState.COMPLETED for predecessor in predecessors):
        raise GovernedDependenciesIncomplete()
    try:
        await governed_evidence_service.passing_evaluation_ids(session, predecessors)
    except governed_evidence_service.EvidenceInvalid as exc:
        raise GovernedDependenciesIncomplete() from exc


async def resolve_evaluation_config(
    session: AsyncSession,
    *,
    task: Task,
    executor: Agent,
    request_overlay: EvaluationConfig | None,
) -> ResolvedEvaluationConfig | None:
    """Resolve immutable governed criteria plus a strictly additive request overlay."""
    try:
        specs, sources = merge_rubric_specs(
            task.acceptance_criteria if task.acceptance_criteria is not None else [],
            request_overlay.rubric_specs if request_overlay else [],
        )
    except RubricSpecError as exc:
        raise EvaluationConfigConflict(str(exc)) from exc

    persisted_evaluator_id = task.evaluator_agent_id
    requested_evaluator_id = request_overlay.evaluator_agent_id if request_overlay else None
    if (
        persisted_evaluator_id is not None
        and requested_evaluator_id is not None
        and persisted_evaluator_id != requested_evaluator_id
    ):
        raise EvaluationConfigConflict("requested evaluator conflicts with governed evaluator")
    evaluator_agent_id = persisted_evaluator_id or requested_evaluator_id
    if evaluator_agent_id is not None:
        evaluator = await session.get(Agent, evaluator_agent_id)
        if (
            evaluator is None
            or evaluator.organization_id != task.organization_id
            or evaluator.status != AgentStatus.ACTIVE
            or evaluator.kind != AgentKind.AI
            or evaluator.default_role not in {AgentRole.EVALUATOR, AgentRole.EITHER}
            or not evaluator.provider
        ):
            raise EvaluationConfigConflict("evaluator is unavailable or not evaluator-capable")
        if evaluator.id == executor.id:
            raise EvaluationConfigConflict("evaluator agent must differ from the executor")
        if persisted_evaluator_id is not None:
            evaluator_capabilities = set(
                (
                    await session.execute(
                        select(AgentCapability.capability).where(
                            AgentCapability.organization_id == task.organization_id,
                            AgentCapability.agent_id == evaluator.id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if "evaluation.rubric" not in evaluator_capabilities:
                raise EvaluationConfigConflict(
                    "governed evaluator no longer has the evaluation.rubric capability"
                )

    governed = task.source_plan_id is not None
    requested_max = request_overlay.max_remediations if request_overlay else None
    if governed:
        max_remediations = task.max_remediations
        if requested_max is not None:
            max_remediations = min(max_remediations, requested_max)
    else:
        max_remediations = requested_max if requested_max is not None else task.max_remediations

    if not specs and evaluator_agent_id is None:
        return None
    if persisted_evaluator_id is not None and "persisted" not in sources:
        sources.insert(0, "persisted")
    if requested_evaluator_id is not None and "request" not in sources:
        sources.append("request")
    return ResolvedEvaluationConfig(
        rubric_specs=specs,
        rubric_sha256=rubric_sha256(specs),
        evaluator_agent_id=evaluator_agent_id,
        max_remediations=max_remediations,
        sources=sources,
    )


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
    evaluation: EvaluationConfig | None = None,
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
    await _require_active_governed_project(session, task)
    await _require_governed_dependencies_complete(session, task)
    executor = await _require_executable(session, task)
    await resolve_evaluation_config(
        session, task=task, executor=executor, request_overlay=evaluation
    )
    if task.source_plan_id is not None:
        await _move_governed_to_queued(
            session,
            task,
            actor_id=actor_id,
            actor_type=actor_type,
        )
    else:
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

    Persisted task criteria are always enforced. A request-level ``evaluation``
    may add criteria or tighten remediation, but cannot weaken governed policy.
    If no persisted or request-level policy exists, a successful run completes
    without grading (the legacy Phase-5 behavior).
    """
    await _require_active_governed_project(session, task)
    await _require_governed_dependencies_complete(session, task)
    agent = await _require_executable(session, task)
    effective_evaluation = await resolve_evaluation_config(
        session, task=task, executor=agent, request_overlay=evaluation
    )
    evaluation_context = (
        {
            "rubric_specs": effective_evaluation.rubric_specs,
            "rubric_sha256": effective_evaluation.rubric_sha256,
            "evaluator_agent_id": (
                str(effective_evaluation.evaluator_agent_id)
                if effective_evaluation.evaluator_agent_id
                else None
            ),
            "max_remediations": effective_evaluation.max_remediations,
            "sources": effective_evaluation.sources,
        }
        if effective_evaluation
        else None
    )

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
    remediation_of: uuid.UUID | None = None
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

    first_attempt_claimed = task.source_plan_id is not None
    if first_attempt_claimed:
        await _claim_governed_execution(
            session,
            task,
            actor_id=actor_id,
            actor_type=actor_type,
        )
        # Persist the exclusive RUNNING claim before any provider or tool can
        # produce an external side effect. A later failure may leave recovery
        # work, but it cannot erase the claim and silently execute twice.
        await session.commit()
    else:
        await _move_to_queued(session, task, actor_id=actor_id, actor_type=actor_type)

    while True:
        attempt += 1
        if first_attempt_claimed:
            first_attempt_claimed = False
        else:
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
                    evaluation=evaluation_context,
                    remediation_of=remediation_of,
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
                    evaluation=evaluation_context,
                    remediation_of=remediation_of,
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
            evaluation=evaluation_context,
            remediation_of=remediation_of,
            tokens_used=result.tokens_used,
            cost_estimate=result.cost_estimate,
        )
        execution_ids.append(execution_id)
        await _transition(
            session, task, ExecutionState.EVALUATING, actor_id=actor_id, actor_type=actor_type
        )

        if effective_evaluation is None:
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
            await session.get(Agent, effective_evaluation.evaluator_agent_id)
            if effective_evaluation.evaluator_agent_id
            else None
        )
        ev = await evaluation_service.evaluate_execution(
            session,
            execution=execution,
            rubric_specs=effective_evaluation.rubric_specs,
            evaluator_agent=evaluator_agent,
            rubric_source="+".join(effective_evaluation.sources),
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
                max_remediations=effective_evaluation.max_remediations,
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
            remediation_of = execution_id
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
    evaluation: dict | None = None,
    remediation_of: uuid.UUID | None = None,
    tokens_used: int = 0,
    cost_estimate: float = 0.0,
) -> uuid.UUID:
    project = await project_lock_service.lock_project(
        session,
        project_id=task.project_id,
        organization_id=task.organization_id,
        require_open=True,
    )
    if project is None:
        raise ValueError("project not found")

    input_context: dict = {"prompt_chars": prompt_chars}
    if handoff:
        input_context["handoff"] = handoff
    if evaluation:
        input_context["evaluation"] = evaluation
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
        remediation_of=remediation_of,
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
    if task.source_plan_id is not None:
        raise GovernedAssignmentLocked()
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
