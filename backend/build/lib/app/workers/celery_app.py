"""Celery application (MVP worker layer).

Per ADR-0002 this is confined behind the WorkflowEngine port; domain code never
imports Celery directly. A trivial health task is provided so the worker is
verifiable in Phase 1; real execution tasks arrive in Phase 5.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "agenticubed",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    # Task modules must be named explicitly: a worker started with
    # `-A app.workers.celery_app` registers nothing otherwise, and messages
    # for execution.run would die as unregistered-task errors.
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="health.ping")
def health_ping() -> str:
    """Liveness task; returns a constant so the worker round-trip is testable."""
    return "pong"
