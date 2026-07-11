"""Resumable project-run orchestration.

``start_project_run`` opens a new run against a project (flush-only, no commit).
``advance_project_run`` selects exactly one dispatchable task, executes it via
``execution_service``, persists the resulting TaskExecution, and updates run
state (flush-only, no commit).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProjectRunStatus
from app.core.roles import ActorType
from app.models.project import Project
from app.models.project_run import ProjectRun
from app.models.task import Task
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service


class NotFound(Exception):
    pass


#: Task states from which ``execute_task`` can make progress.
_RUNNABLE_STATES: frozenset[ExecutionState] = frozenset(
    {
        ExecutionState.PLANNED,
        ExecutionState.READY,
        ExecutionState.FAILED,
        ExecutionState.BLOCKED,
    }
)

#: Run states that require no further automated work.
_TERMINAL_RUN_STATES: frozenset[ProjectRunStatus] = frozenset(
    {ProjectRunStatus.COMPLETED, ProjectRunStatus.CANCELLED}
)


async def start_project_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    initiated_by: uuid.UUID | None,
) -> ProjectRun:
    """Validate the project exists, create a new run, and flush (no commit)."""
    project = await session.get(Project, project_id)
    if project is None:
        raise NotFound(f"project {project_id} not found")

    run = ProjectRun(
        project_id=project_id,
        initiated_by=initiated_by,
        status=ProjectRunStatus.RUNNING,
    )
    session.add(run)
    await session.flush()
    return run


async def advance_project_run(
    session: AsyncSession,
    run_id: uuid.UUID,
) -> ProjectRun:
    """Reload run, execute exactly one runnable task, update run state, and flush.

    Returns the run unchanged when it is already in a terminal state.
    Does not commit. Does not catch broad Exception.
    """
    run = await session.get(ProjectRun, run_id)
    if run is None:
        raise NotFound(f"project run {run_id} not found")

    if run.status in _TERMINAL_RUN_STATES:
        return run

    stmt = (
        select(Task)
        .where(
            Task.project_id == run.project_id,
            Task.assigned_agent_id.is_not(None),
            Task.status.in_(list(_RUNNABLE_STATES)),
        )
        .order_by(Task.priority, Task.order_index)
        .limit(1)
    )
    task: Task | None = (await session.execute(stmt)).scalar_one_or_none()

    if task is None:
        run.status = ProjectRunStatus.COMPLETED
        await session.flush()
        return run

    await execution_service.execute_task(
        session,
        task=task,
        actor_id=run.initiated_by,
        actor_type=ActorType.SYSTEM,
    )

    # Re-check for remaining runnable tasks after execution.
    remaining: Task | None = (
        await session.execute(
            select(Task)
            .where(
                Task.project_id == run.project_id,
                Task.assigned_agent_id.is_not(None),
                Task.status.in_(list(_RUNNABLE_STATES)),
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if remaining is None:
        run.status = ProjectRunStatus.COMPLETED

    await session.flush()
    return run
