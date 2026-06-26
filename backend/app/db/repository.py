"""Repository base that enforces organization scoping.

Every read/write goes through a repository bound to a single organization_id, so
cross-tenant access is impossible by construction at this layer (security-model
§1). Services never issue raw cross-org queries.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class OrgScopedRepository(Generic[ModelT]):
    """CRUD scoped to one organization. Subclasses set ``model``."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession, organization_id: uuid.UUID) -> None:
        self.session = session
        self.organization_id = organization_id

    def _scoped(self):
        # Every model in scope carries organization_id.
        return select(self.model).where(
            self.model.organization_id == self.organization_id  # type: ignore[attr-defined]
        )

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = self._scoped().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(self) -> list[ModelT]:
        return list((await self.session.execute(self._scoped())).scalars().all())

    def add(self, entity: ModelT) -> ModelT:
        # Guard against an org_id mismatch sneaking in.
        if getattr(entity, "organization_id") != self.organization_id:  # noqa: B009
            raise ValueError("entity organization_id does not match repository scope")
        self.session.add(entity)
        return entity
