"""Celery task that runs a task execution in a worker.

The unit of work is ``execution_service.execute_task`` — the same code the inline
path runs — so the worker engine is just transport. Dispatch parameters
(attempts, timeout, evaluation config, actor) ride the Celery message as a
JSON-safe dict so the worker runs with the caller's exact intent. The session
factory is indirected so tests can run this task against the test DB.

After a task COMPLETES, the worker runs a scheduling pass (WS-2) so successor
tasks whose dependencies are now satisfied get dispatched without another API
call — this is what keeps a started project moving.
"""

from __future__ import annotations

import asyncio
import uuid

from app.core.roles import ActorType
from app.models.task import Task
from app.orchestration.engines import get_workflow_engine
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service, project_lock_service, scheduler_service
from app.workers.celery_app import celery_app

# Overridable for tests; defaults to the application's async session factory.
_session_factory = None


def set_session_factory(factory) -> None:
    global _session_factory
    _session_factory = factory


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        from app.db.session import SessionFactory

        _session_factory = SessionFactory
    return _session_factory


def _parse_dispatch_params(params: dict) -> dict:
    """Inverse of build_dispatch_params: kwargs for execute_task."""
    kwargs: dict = {
        "actor_id": uuid.UUID(params["actor_id"]) if params.get("actor_id") else None,
        "actor_type": ActorType(params.get("actor_type", ActorType.SYSTEM.value)),
        "max_attempts": int(params.get("max_attempts", 2)),
        "timeout_s": float(params.get("timeout_s", 30.0)),
    }
    raw_eval = params.get("evaluation")
    if raw_eval is not None:
        raw_max_remediations = raw_eval.get("max_remediations")
        kwargs["evaluation"] = execution_service.EvaluationConfig(
            rubric_specs=(raw_eval["rubric_specs"] if "rubric_specs" in raw_eval else []),
            evaluator_agent_id=(
                uuid.UUID(raw_eval["evaluator_agent_id"])
                if raw_eval.get("evaluator_agent_id")
                else None
            ),
            max_remediations=(
                int(raw_max_remediations) if raw_max_remediations is not None else None
            ),
        )
    return kwargs


async def _run(task_id: uuid.UUID, params: dict) -> None:
    factory = _get_session_factory()
    async with factory() as session:
        task = await session.get(Task, task_id)
        if task is None:
            return
        parsed = _parse_dispatch_params(params)
        try:
            await execution_service.execute_task(session, task=task, **parsed)
        except (execution_service.AlreadyQueued, project_lock_service.ProjectClosed):
            # Duplicate broker deliveries are expected in at-least-once
            # transports. The persisted governed claim is the authority.
            await session.rollback()
            return
        await session.commit()

        if task.status != ExecutionState.COMPLETED:
            return
        engine = get_workflow_engine()
        if engine is None:
            # Worker configured inline (misconfiguration): nothing to advance.
            return
        # Scheduler-triggered dispatches act as the system, inheriting the
        # chain's attempt/timeout options but not task-specific evaluation.
        successor_params = execution_service.build_dispatch_params(
            actor_id=None,
            actor_type=ActorType.SYSTEM,
            max_attempts=parsed["max_attempts"],
            timeout_s=parsed["timeout_s"],
            evaluation=None,
        )
        await scheduler_service.dispatch_ready(
            session,
            project_id=task.project_id,
            engine=engine,
            params=successor_params,
            actor_id=None,
            actor_type=ActorType.SYSTEM,
        )


@celery_app.task(name="execution.run")
def run_task_execution(task_id: str, params: dict | None = None) -> str:
    """Worker entrypoint: run one task's execution end-to-end."""
    asyncio.run(_run(uuid.UUID(task_id), params or {}))
    return task_id
