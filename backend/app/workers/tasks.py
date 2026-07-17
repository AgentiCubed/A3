"""Celery task that runs a task execution in a worker.

The unit of work is ``execution_service.execute_task`` — the same code the inline
path runs — so the worker engine is just transport. Dispatch parameters
(attempts, timeout, evaluation config, actor) ride the Celery message as a
JSON-safe dict so the worker runs with the caller's exact intent. The session
factory is indirected so tests can run this task against the test DB.
"""

from __future__ import annotations

import asyncio
import uuid

from app.core.roles import ActorType
from app.models.task import Task
from app.services import execution_service
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
        kwargs["evaluation"] = execution_service.EvaluationConfig(
            rubric_specs=raw_eval.get("rubric_specs") or [],
            evaluator_agent_id=(
                uuid.UUID(raw_eval["evaluator_agent_id"])
                if raw_eval.get("evaluator_agent_id")
                else None
            ),
            max_remediations=int(raw_eval.get("max_remediations", 1)),
        )
    return kwargs


async def _run(task_id: uuid.UUID, params: dict) -> None:
    factory = _get_session_factory()
    async with factory() as session:
        task = await session.get(Task, task_id)
        if task is None:
            return
        await execution_service.execute_task(session, task=task, **_parse_dispatch_params(params))
        await session.commit()


@celery_app.task(name="execution.run")
def run_task_execution(task_id: str, params: dict | None = None) -> str:
    """Worker entrypoint: run one task's execution end-to-end."""
    asyncio.run(_run(uuid.UUID(task_id), params or {}))
    return task_id
