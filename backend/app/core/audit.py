"""Audit sink — the single place audit events are written.

Services call ``record_audit`` inside their own transaction so the state change
and its audit row commit atomically. before/after payloads are redacted here so
no secret can ever land in an audit row.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redaction import redact
from app.core.roles import ActorType
from app.models.audit_event import AuditEvent


async def record_audit(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    actor_type: ActorType,
    action: str,
    entity_type: str,
    actor_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditEvent:
    """Add an AuditEvent to the current transaction (does not commit)."""
    event = AuditEvent(
        organization_id=organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=redact(before) if before is not None else None,
        after=redact(after) if after is not None else None,
        ip=ip,
    )
    session.add(event)
    return event
