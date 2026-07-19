"""WorkflowEngine implementations (the durable worker seam).

``CeleryWorkflowEngine`` implements the provider-neutral ``WorkflowEngine`` port
over Celery + Redis. A future ``TemporalWorkflowEngine`` would implement the same
port without touching ``execution_service`` (ADR-0002). The inline path (API
default) simply awaits ``execution_service.execute_task`` directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.orchestration.ports import EngineState, EngineStatus

_CELERY_STATE_MAP = {
    "PENDING": EngineState.PENDING,
    "STARTED": EngineState.RUNNING,
    "RETRY": EngineState.RUNNING,
    "SUCCESS": EngineState.DONE,
    "FAILURE": EngineState.FAILED,
    "REVOKED": EngineState.CANCELLED,
}


class CeleryWorkflowEngine:
    """Submit/track task executions via Celery. Implements WorkflowEngine."""

    name = "celery"

    def submit_execution(self, work_id: UUID, params: dict[str, Any] | None = None) -> str:
        from app.workers.tasks import run_task_execution

        async_result = run_task_execution.delay(str(work_id), params or {})
        return async_result.id

    def signal_cancel(self, handle: str) -> None:
        from app.workers.celery_app import celery_app

        celery_app.control.revoke(handle, terminate=True)

    def get_status(self, handle: str) -> EngineStatus:
        from celery.result import AsyncResult

        from app.workers.celery_app import celery_app

        result = AsyncResult(handle, app=celery_app)
        state = _CELERY_STATE_MAP.get(result.state, EngineState.UNKNOWN)
        return EngineStatus(state=state, detail=result.state)


@lru_cache
def get_workflow_engine() -> CeleryWorkflowEngine | None:
    """Engine for async dispatch, or None when the backend is "inline".

    Inline mode has no engine object: the API awaits ``execute_task`` in the
    request (dev/test behavior). Celery mode queues through this engine and
    the request returns before execution starts.
    """
    if get_settings().workflow_engine_backend == "celery":
        return CeleryWorkflowEngine()
    return None


def reset_workflow_engine() -> None:
    """Test hook: drop the cached engine so settings changes take effect."""
    get_workflow_engine.cache_clear()
