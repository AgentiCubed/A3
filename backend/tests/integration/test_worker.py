"""Worker-layer integration test.

Runs the Celery health task in eager mode so the task wiring is verified without
a live broker. Real execution tasks (Phase 5) will use the same pattern plus a
broker fixture.
"""

from __future__ import annotations

from app.workers.celery_app import celery_app, health_ping


def test_health_ping_eager():
    celery_app.conf.task_always_eager = True
    result = health_ping.delay()
    assert result.get(timeout=5) == "pong"
