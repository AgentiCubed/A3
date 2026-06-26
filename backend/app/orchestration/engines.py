"""WorkflowEngine implementations (the durable worker seam).

``CeleryWorkflowEngine`` implements the provider-neutral ``WorkflowEngine`` port
over Celery + Redis. A future ``TemporalWorkflowEngine`` would implement the same
port without touching ``execution_service`` (ADR-0002). The inline path (API
default) simply awaits ``execution_service.execute_task`` directly.
"""

from __future__ import annotations

from uuid import UUID

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

    def submit_execution(self, execution_id: UUID) -> str:
        from app.workers.tasks import run_task_execution

        async_result = run_task_execution.delay(str(execution_id))
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
