"""Per-project serialization for closeout and acceptance-affecting writes."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProjectStatus
from app.models.project import Project


class ProjectClosed(Exception):
    """Acceptance-affecting evidence cannot be added after project closure."""


async def lock_project(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    organization_id: uuid.UUID | None = None,
    require_open: bool = False,
) -> Project | None:
    """Acquire the project's write lock on PostgreSQL and SQLite.

    The no-op UPDATE takes a row lock in PostgreSQL and a write lock in SQLite,
    allowing the same concurrency contract to be exercised by hermetic tests.
    Explicitly preserving ``updated_at`` keeps lock acquisition metadata-neutral.
    """
    predicates = [Project.id == project_id]
    if organization_id is not None:
        predicates.append(Project.organization_id == organization_id)
    if require_open:
        predicates.append(Project.status != ProjectStatus.CLOSED)

    result = await session.execute(
        update(Project).where(*predicates)
        # Self-assign to acquire the write lock without changing project data.
        .values(status=Project.status, updated_at=Project.updated_at)
    )
    if result.rowcount != 1:
        project = await session.scalar(
            select(Project).where(
                Project.id == project_id,
                *(
                    [Project.organization_id == organization_id]
                    if organization_id is not None
                    else []
                ),
            )
        )
        if require_open and project is not None and project.status == ProjectStatus.CLOSED:
            raise ProjectClosed()
        return None

    return await session.scalar(
        select(Project).where(Project.id == project_id).execution_options(populate_existing=True)
    )
