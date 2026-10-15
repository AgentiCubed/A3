"""Audit sink — the single place audit events are written.

Services call ``record_audit`` inside their own transaction so the state change
and its audit row commit atomically. before/after payloads are redacted here so
no secret can ever land in an audit row.

The same call also publishes a ``DomainEvent`` to the live EventBus so any
audited change is streamable in real time. Publication is best-effort and
pre-commit: the stream is an advisory live hint, never a substitute for the
audit trail. A publish failure must never break the business transaction.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redaction import redact
from app.core.roles import ActorType
from app.models.audit_event import AuditEvent
from app.orchestration.ports import DomainEvent

logger = structlog.get_logger(__name__)


async def record_audit(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    actor_type: ActorType,
    action: str,
    entity_type: str,
    actor_id: uuid.UUID | None = None,
    entity_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditEvent:
    """Add an AuditEvent to the current transaction (does not commit).

    ``project_id`` is not stored on the audit row (schema unchanged); it scopes
    the corresponding live DomainEvent to a project stream.
    """
    redacted_before = redact(before) if before is not None else None
    redacted_after = redact(after) if after is not None else None
    event = AuditEvent(
        organization_id=organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=redacted_before,
        after=redacted_after,
        ip=ip,
    )
    session.add(event)

    try:
        from app.orchestration.adapters.event_bus import get_event_bus

        await get_event_bus().publish(
            DomainEvent(
                organization_id=organization_id,
                project_id=project_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_type=actor_type.value if hasattr(actor_type, "value") else str(actor_type),
                actor_id=actor_id,
                occurred_at=datetime.now(UTC),
                payload=redacted_after or {},
            )
        )
    except Exception:  # noqa: BLE001 - the stream must never break the transaction
        logger.debug("event_publish_failed", action=action, entity_type=entity_type)

    return event
