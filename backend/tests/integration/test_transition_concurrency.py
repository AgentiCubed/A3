"""Dispatch-transition concurrency for legacy (non-plan) tasks (ADR-0008).

The governed path has claimed transitions atomically since WS-6; these tests
prove the same guarantee now holds for legacy tasks against a real database:
two sessions holding the same task can both pass the in-memory status check,
but the conditional UPDATE makes the persisted row the arbiter — exactly one
dispatcher wins, the loser gets ``AlreadyQueued``, and the task can never be
queued or started twice.
"""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.core.roles import ActorType
from app.models.audit_event import AuditEvent
from app.models.task import Task
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service
from tests.conftest import TestSessionFactory


def _auth(client) -> dict[str, str]:
    email = f"cc-{uuid.uuid4().hex[:10]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _legacy_task(client, headers) -> str:
    """A plain (non-plan) task with an executable mock agent assigned."""
    pid = client.post(
        "/api/v1/projects", json={"name": "P", "objective": "o"}, headers=headers
    ).json()["id"]
    task_id = client.post(
        f"/api/v1/projects/{pid}/tasks", json={"title": "T"}, headers=headers
    ).json()["id"]
    agent_id = client.post(
        "/api/v1/agents",
        json={"name": "Worker", "kind": "ai", "provider": "mock"},
        headers=headers,
    ).json()["id"]
    resp = client.patch(
        f"/api/v1/projects/{pid}/tasks/{task_id}/assign",
        json={"agent_id": agent_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    return task_id


def _transition_audits(task_id: str) -> list[tuple[str | None, str | None]]:
    async def _query():
        async with TestSessionFactory() as session:
            rows = (
                (
                    await session.execute(
                        select(AuditEvent)
                        .where(
                            AuditEvent.action == "task.transition",
                            AuditEvent.entity_id == uuid.UUID(task_id),
                        )
                        .order_by(AuditEvent.occurred_at)
                    )
                )
                .scalars()
                .all()
            )
            return [(r.before.get("status"), r.after.get("status")) for r in rows]

    return asyncio.run(_query())


def test_stale_session_cannot_double_queue_a_legacy_task(client):
    """Two dispatchers race the QUEUED claim; the persisted row arbitrates.

    Both sessions load the task while it is PLANNED, so both pass the
    in-memory ``AlreadyQueued`` pre-check. Under the old read-then-write
    transition both would have queued it (and submitted two worker messages);
    with the conditional claim exactly one wins.
    """
    headers = _auth(client)
    task_id = _legacy_task(client, headers)

    async def _race():
        async with TestSessionFactory() as sa, TestSessionFactory() as sb:
            task_a = await sa.get(Task, uuid.UUID(task_id))
            task_b = await sb.get(Task, uuid.UUID(task_id))  # stale after A commits
            assert task_a.status == ExecutionState.PLANNED
            assert task_b.status == ExecutionState.PLANNED

            await execution_service.queue_task(
                sa, task=task_a, actor_id=None, actor_type=ActorType.SYSTEM
            )
            await sa.commit()

            try:
                await execution_service.queue_task(
                    sb, task=task_b, actor_id=None, actor_type=ActorType.SYSTEM
                )
                await sb.commit()
                return None
            except execution_service.AlreadyQueued as exc:
                await sb.rollback()
                return exc

    loser = asyncio.run(_race())
    assert isinstance(loser, execution_service.AlreadyQueued)

    async def _status():
        async with TestSessionFactory() as session:
            return await session.scalar(select(Task.status).where(Task.id == uuid.UUID(task_id)))

    assert asyncio.run(_status()) == ExecutionState.QUEUED
    # Exactly one dispatcher's walk was recorded: planned→ready→queued, once.
    assert _transition_audits(task_id) == [("planned", "ready"), ("ready", "queued")]


def test_stale_session_cannot_double_start_a_queued_legacy_task(client):
    """Two workers race the RUNNING claim on the same QUEUED task.

    This is the double-execution hazard (e.g. broker redelivery): both
    sessions see QUEUED, but only one can claim QUEUED→RUNNING and reach the
    provider; the loser gets ``AlreadyQueued`` before any external effect.
    """
    headers = _auth(client)
    task_id = _legacy_task(client, headers)

    async def _race():
        async with TestSessionFactory() as setup:
            task = await setup.get(Task, uuid.UUID(task_id))
            await execution_service.queue_task(
                setup, task=task, actor_id=None, actor_type=ActorType.SYSTEM
            )
            await setup.commit()

        async with TestSessionFactory() as sa, TestSessionFactory() as sb:
            task_a = await sa.get(Task, uuid.UUID(task_id))
            task_b = await sb.get(Task, uuid.UUID(task_id))
            assert task_a.status == ExecutionState.QUEUED
            assert task_b.status == ExecutionState.QUEUED

            await execution_service._claim_execution(
                sa, task_a, actor_id=None, actor_type=ActorType.SYSTEM
            )
            await sa.commit()

            try:
                await execution_service._claim_execution(
                    sb, task_b, actor_id=None, actor_type=ActorType.SYSTEM
                )
                await sb.commit()
                return None
            except execution_service.AlreadyQueued as exc:
                await sb.rollback()
                return exc

    loser = asyncio.run(_race())
    assert isinstance(loser, execution_service.AlreadyQueued)

    async def _status():
        async with TestSessionFactory() as session:
            return await session.scalar(select(Task.status).where(Task.id == uuid.UUID(task_id)))

    assert asyncio.run(_status()) == ExecutionState.RUNNING
