"""Serialize project closure with writes that can change acceptance evidence.

Every evidence writer and the close path updates the same ``Project`` row
before inspecting or changing acceptance data. PostgreSQL therefore uses a
per-project row lock, while SQLite acquires a real write lock even though it
ignores ``SELECT ... FOR UPDATE``. The revision is also an optimistic guard
against a stale acceptance snapshot reaching the final close update.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProjectStatus
from app.models.project import Project


class ProjectClosed(Exception):
    """Acceptance-changing work was attempted after project closure."""


class ProjectNotFound(Exception):
    """The project boundary could not be found in the expected organization."""


async def _reject_missing_or_closed(
    session: AsyncSession, *, project_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    status = await session.scalar(
        select(Project.status).where(
            Project.id == project_id,
            Project.organization_id == org_id,
        )
    )
    if status == ProjectStatus.CLOSED:
        raise ProjectClosed()
    raise ProjectNotFound()


async def claim_acceptance_write(
    session: AsyncSession, *, project_id: uuid.UUID, org_id: uuid.UUID
) -> int:
    """Claim one acceptance-changing write and return its new revision.

    The conditional update is part of the caller's transaction. If close wins
    first, the status predicate rejects the late write. If a writer wins first,
    close waits for it and evaluates the newly committed evidence.
    """
    revision = await session.scalar(
        update(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == org_id,
            Project.status != ProjectStatus.CLOSED,
        )
        .values(acceptance_revision=Project.acceptance_revision + 1)
        .returning(Project.acceptance_revision)
        .execution_options(synchronize_session=False)
    )
    if revision is None:
        await _reject_missing_or_closed(session, project_id=project_id, org_id=org_id)
    return int(revision)


async def lock_acceptance_for_close(
    session: AsyncSession, *, project_id: uuid.UUID, org_id: uuid.UUID
) -> int:
    """Lock the acceptance boundary without advancing the evidence revision."""
    revision = await session.scalar(
        update(Project)
        .where(
            Project.id == project_id,
            Project.organization_id == org_id,
            Project.status != ProjectStatus.CLOSED,
        )
        .values(acceptance_revision=Project.acceptance_revision)
        .returning(Project.acceptance_revision)
        .execution_options(synchronize_session=False)
    )
    if revision is None:
        await _reject_missing_or_closed(session, project_id=project_id, org_id=org_id)
    return int(revision)
