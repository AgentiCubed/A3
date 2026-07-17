"""Dependency-aware runtime scheduling (WS-2).

A task is *dispatchable* when it is PLANNED or READY, is assigned an AI agent,
and every predecessor task is COMPLETED. For runtime ordering every dependency
type gates on predecessor completion; CPM type/lag semantics apply to timeline
math (``app.scheduling``), not to dispatch. Tasks that are unassigned, human,
or dependency-blocked are simply not selected — and keep gating their
successors until they complete.

Both consumers run the same work-conserving pass, dispatching every
dispatchable task up to the per-project concurrency cap
(``SCHEDULER_MAX_PARALLEL`` minus tasks already in flight):

- ``POST /projects/{id}/start`` kicks the loop off;
- the worker calls back after finishing a task to advance the chain.

Inline mode has no worker, so ``run_inline`` chains passes in-request until no
task is dispatchable — a seeded A→B→C chain completes from a single call.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import AgentKind
from app.core.roles import ActorType
from app.models.agent import Agent
from app.models.task import Task, TaskDependency
from app.orchestration.ports import WorkflowEngine
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service

_IN_FLIGHT = (ExecutionState.QUEUED, ExecutionState.RUNNING, ExecutionState.EVALUATING)
_SCHEDULABLE = (ExecutionState.PLANNED, ExecutionState.READY)


@dataclass(frozen=True)
class TaskOutcome:
    task_id: uuid.UUID
    status: ExecutionState


async def find_dispatchable(session: AsyncSession, project_id: uuid.UUID) -> list[Task]:
    """Return dispatchable tasks, in order_index order, up to spare capacity."""
    tasks = list(
        (
            await session.execute(
                select(Task).where(Task.project_id == project_id).order_by(Task.order_index)
            )
        )
        .scalars()
        .all()
    )
    capacity = get_settings().scheduler_max_parallel - sum(
        1 for t in tasks if t.status in _IN_FLIGHT
    )
    if capacity <= 0:
        return []

    deps = (
        (
            await session.execute(
                select(TaskDependency).where(TaskDependency.project_id == project_id)
            )
        )
        .scalars()
        .all()
    )
    predecessors: dict[uuid.UUID, set[uuid.UUID]] = {}
    for d in deps:
        predecessors.setdefault(d.successor_task_id, set()).add(d.predecessor_task_id)
    completed = {t.id for t in tasks if t.status == ExecutionState.COMPLETED}

    assigned_ids = {t.assigned_agent_id for t in tasks if t.assigned_agent_id is not None}
    ai_agent_ids: set[uuid.UUID] = set()
    if assigned_ids:
        rows = await session.execute(
            select(Agent.id).where(Agent.id.in_(assigned_ids), Agent.kind == AgentKind.AI)
        )
        ai_agent_ids = set(rows.scalars().all())

    eligible = [
        t
        for t in tasks
        if t.status in _SCHEDULABLE
        and not t.is_human_task
        and t.assigned_agent_id in ai_agent_ids
        and predecessors.get(t.id, set()) <= completed
    ]
    return eligible[:capacity]


async def dispatch_ready(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    engine: WorkflowEngine,
    params: dict,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> list[TaskOutcome]:
    """Asynchronous pass (celery mode): queue and submit every dispatchable task.

    Follows the same rules as the single-task dispatch endpoint: commit the
    QUEUED state before submitting so the worker sees it, and on submit failure
    park the task BLOCKED (re-dispatchable) rather than leaving it stuck.
    """
    dispatched: list[TaskOutcome] = []
    for task in await find_dispatchable(session, project_id):
        try:
            await execution_service.queue_task(
                session, task=task, actor_id=actor_id, actor_type=actor_type
            )
        except execution_service.AlreadyQueued:  # raced by a concurrent dispatcher
            continue
        await session.commit()
        try:
            engine.submit_execution(task.id, params)
        except Exception:  # noqa: BLE001 - broker down; park and keep scheduling
            await execution_service.transition_task(
                session,
                task,
                ExecutionState.BLOCKED,
                actor_id=actor_id,
                actor_type=actor_type,
                reason="engine submit failed during scheduling",
            )
            await session.commit()
            continue
        dispatched.append(TaskOutcome(task_id=task.id, status=task.status))
    return dispatched


async def run_inline(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
    max_attempts: int,
    timeout_s: float,
) -> list[TaskOutcome]:
    """Inline pass: execute dispatchable tasks in-request until none remain.

    Each completed task can unlock its successors, so the loop re-selects after
    every batch and a whole dependency chain runs from one call. Terminates
    because ``execute_task`` always leaves a task in a non-schedulable state
    (COMPLETED, BLOCKED, or AWAITING_APPROVAL).
    """
    outcomes: dict[uuid.UUID, ExecutionState] = {}
    while True:
        batch = await find_dispatchable(session, project_id)
        if not batch:
            break
        for task in batch:
            result = await execution_service.execute_task(
                session,
                task=task,
                actor_id=actor_id,
                actor_type=actor_type,
                max_attempts=max_attempts,
                timeout_s=timeout_s,
            )
            outcomes[task.id] = result.final_state
    return [TaskOutcome(task_id=tid, status=state) for tid, state in outcomes.items()]
