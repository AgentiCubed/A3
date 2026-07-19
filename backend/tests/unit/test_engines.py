"""CeleryWorkflowEngine — the durable-dispatch adapter over Celery, and the
settings-driven ``get_workflow_engine`` accessor.

Celery and its broker are never touched: the task, the app control channel, and
``AsyncResult`` are all stubbed, so these remain hermetic unit tests of the
adapter's own logic (delegation, cancel semantics, and state mapping).
"""

from __future__ import annotations

import uuid

import pytest

from app.orchestration import engines
from app.orchestration.engines import (
    CeleryWorkflowEngine,
    get_workflow_engine,
    reset_workflow_engine,
)
from app.orchestration.ports import EngineState


def test_submit_execution_delegates_to_celery_task(monkeypatch):
    captured: dict = {}

    class _AsyncResult:
        id = "handle-123"

    class _Task:
        def delay(self, work_id, params):
            captured["work_id"] = work_id
            captured["params"] = params
            return _AsyncResult()

    import app.workers.tasks as tasks_mod

    monkeypatch.setattr(tasks_mod, "run_task_execution", _Task())

    work_id = uuid.uuid4()
    handle = CeleryWorkflowEngine().submit_execution(work_id, {"attempts": 2})

    assert handle == "handle-123"
    assert captured["work_id"] == str(work_id)  # JSON-safe stringified id
    assert captured["params"] == {"attempts": 2}


def test_submit_execution_defaults_params_to_empty_dict(monkeypatch):
    captured: dict = {}

    class _AsyncResult:
        id = "h"

    class _Task:
        def delay(self, work_id, params):
            captured["params"] = params
            return _AsyncResult()

    import app.workers.tasks as tasks_mod

    monkeypatch.setattr(tasks_mod, "run_task_execution", _Task())

    CeleryWorkflowEngine().submit_execution(uuid.uuid4())
    assert captured["params"] == {}


def test_signal_cancel_revokes_with_terminate(monkeypatch):
    captured: dict = {}

    class _Control:
        def revoke(self, handle, terminate):
            captured["handle"] = handle
            captured["terminate"] = terminate

    class _App:
        control = _Control()

    import app.workers.celery_app as celery_mod

    monkeypatch.setattr(celery_mod, "celery_app", _App())

    CeleryWorkflowEngine().signal_cancel("handle-9")
    assert captured == {"handle": "handle-9", "terminate": True}


@pytest.mark.parametrize(
    "celery_state,expected",
    [
        ("PENDING", EngineState.PENDING),
        ("STARTED", EngineState.RUNNING),
        ("RETRY", EngineState.RUNNING),
        ("SUCCESS", EngineState.DONE),
        ("FAILURE", EngineState.FAILED),
        ("REVOKED", EngineState.CANCELLED),
        ("WEIRD_UNMAPPED_STATE", EngineState.UNKNOWN),
    ],
)
def test_get_status_maps_celery_states(monkeypatch, celery_state, expected):
    import celery.result as celery_result

    class _Result:
        def __init__(self, handle, app=None):
            self.state = celery_state

    monkeypatch.setattr(celery_result, "AsyncResult", _Result)

    status = CeleryWorkflowEngine().get_status("handle")
    assert status.state == expected
    assert status.detail == celery_state  # raw Celery state preserved as detail


class _FakeSettings:
    def __init__(self, backend):
        self.workflow_engine_backend = backend


def test_get_workflow_engine_returns_celery_when_configured(monkeypatch):
    reset_workflow_engine()
    monkeypatch.setattr(engines, "get_settings", lambda: _FakeSettings("celery"))
    try:
        assert isinstance(get_workflow_engine(), CeleryWorkflowEngine)
    finally:
        reset_workflow_engine()


def test_get_workflow_engine_returns_none_for_inline(monkeypatch):
    reset_workflow_engine()
    monkeypatch.setattr(engines, "get_settings", lambda: _FakeSettings("inline"))
    try:
        assert get_workflow_engine() is None
    finally:
        reset_workflow_engine()
