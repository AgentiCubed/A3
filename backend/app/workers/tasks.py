"""Celery task that runs a task execution in a worker.

The unit of work is ``execution_service.execute_task`` — the same code the inline
path runs — so the worker engine is just transport. The session factory is
indirected so tests can run this task (in Celery eager mode) against the test DB.
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


async def _run(task_id: uuid.UUID) -> None:
    factory = _get_session_factory()
    async with factory() as session:
        task = await session.get(Task, task_id)
        if task is None:
            return
        await execution_service.execute_task(
            session, task=task, actor_id=None, actor_type=ActorType.SYSTEM
        )
        await session.commit()


@celery_app.task(name="execution.run")
def run_task_execution(task_id: str) -> str:
    """Worker entrypoint: run one task's execution end-to-end."""
    asyncio.run(_run(uuid.UUID(task_id)))
    return task_id
