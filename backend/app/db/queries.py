"""Small helpers for the org-scoped read patterns repeated across services.

These centralize the two shapes that recur throughout ``app/services``:

* fetch a single entity by id, but only if it belongs to the caller's org, and
* list all rows of a model for one org (optionally with extra filters).

They keep the org-scoping predicate in one place without forcing services onto
the class-based :class:`~app.db.repository.OrgScopedRepository`.
"""

from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import ColumnExpressionArgument, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


async def get_by_org(
    session: AsyncSession,
    model: type[ModelT],
    entity_id: uuid.UUID,
    org_id: uuid.UUID,
) -> ModelT | None:
    """Return the entity if it exists and belongs to ``org_id``, else ``None``."""
    entity = await session.get(model, entity_id)
    if entity is None or entity.organization_id != org_id:  # type: ignore[attr-defined]
        return None
    return entity


async def list_by_org(
    session: AsyncSession,
    model: type[ModelT],
    org_id: uuid.UUID,
    *where: ColumnExpressionArgument[bool],
) -> list[ModelT]:
    """Return all rows of ``model`` for ``org_id`` matching any extra ``where``."""
    stmt = select(model).where(model.organization_id == org_id)  # type: ignore[attr-defined]
    for condition in where:
        stmt = stmt.where(condition)
    return list((await session.execute(stmt)).scalars().all())
