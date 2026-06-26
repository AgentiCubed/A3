"""Audit events are written on material changes and are append-only."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.db.base import ImmutableError
from app.models.audit_event import AuditEvent
from tests.conftest import TestSessionFactory


def _register(client, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={"organization_name": "Acme", "email": email, "password": "supersecret123"},
    )


def test_registration_writes_audit_event(client):
    email = f"audit-{uuid.uuid4().hex[:8]}@example.com"
    reg = _register(client, email)
    org_id = uuid.UUID(reg.json()["organization_id"])

    async def _count() -> int:
        async with TestSessionFactory() as s:
            rows = (
                (
                    await s.execute(
                        select(AuditEvent).where(
                            AuditEvent.organization_id == org_id,
                            AuditEvent.action == "organization.register",
                        )
                    )
                )
                .scalars()
                .all()
            )
            return len(rows)

    import asyncio

    assert asyncio.run(_count()) == 1


async def test_audit_event_cannot_be_updated(session):
    event = AuditEvent(
        organization_id=uuid.uuid4(),
        actor_type="system",
        action="test.event",
        entity_type="Test",
        after={"k": "v"},
    )
    session.add(event)
    await session.commit()

    event.action = "tampered"
    with pytest.raises(ImmutableError):
        await session.commit()


async def test_audit_event_cannot_be_deleted(session):
    event = AuditEvent(
        organization_id=uuid.uuid4(),
        actor_type="system",
        action="test.delete",
        entity_type="Test",
    )
    session.add(event)
    await session.commit()

    await session.delete(event)
    with pytest.raises(ImmutableError):
        await session.commit()


async def test_secret_redacted_in_audit_payload(session):
    from app.core.audit import record_audit
    from app.core.roles import ActorType

    org_id = uuid.uuid4()
    await record_audit(
        session,
        organization_id=org_id,
        actor_type=ActorType.SYSTEM,
        action="config.set",
        entity_type="Agent",
        after={"api_key": "sk-should-not-persist", "model": "x"},
    )
    await session.commit()

    row = (
        await session.execute(select(AuditEvent).where(AuditEvent.organization_id == org_id))
    ).scalar_one()
    assert row.after["api_key"] == "***REDACTED***"
    assert row.after["model"] == "x"
