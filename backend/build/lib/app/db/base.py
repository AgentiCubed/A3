"""SQLAlchemy declarative base and shared column mixins.

Concrete ORM models land in app/models in Phase 2+. The base and mixins are
defined here so migrations and the session layer have a stable import target.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, event, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class ImmutableError(RuntimeError):
    """Raised when application code attempts to UPDATE or DELETE an append-only row."""


class Immutable:
    """Marker mixin for append-only entities (TaskExecution, Evaluation, AuditEvent…).

    A session-level guard (below) rejects any flush that would update or delete an
    instance of an Immutable subclass. Inserts are allowed. This enforces the
    immutability invariant on every backend (SQLite tests included); a Postgres
    trigger in the migrations adds defense-in-depth for direct SQL.
    """


@event.listens_for(Session, "before_flush")
def _block_immutable_mutations(
    session: Session, _flush_context: object, _instances: object
) -> None:
    for obj in session.dirty:
        if isinstance(obj, Immutable) and session.is_modified(obj, include_collections=False):
            raise ImmutableError(f"{type(obj).__name__} is append-only and cannot be updated")
    for obj in session.deleted:
        if isinstance(obj, Immutable):
            raise ImmutableError(f"{type(obj).__name__} is append-only and cannot be deleted")


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CreatedAtMixin:
    """For append-only / immutable tables: created_at only, no updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
