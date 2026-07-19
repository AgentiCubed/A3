"""Shared FastAPI dependencies: DB session, current user/actor, RBAC guard."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.rbac import Action, Actor, authorize
from app.core.roles import ActorType
from app.db.session import get_session
from app.models.project import Project
from app.models.user import User
from app.services import project_service

_bearer = HTTPBearer(auto_error=False)


async def db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(db_session)]


async def get_current_user(
    session: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        claims = security.decode_token(creds.credentials, expected_type="access")
    except security.TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = await session.get(User, uuid.UUID(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found or inactive")
    # The token's org claim must match the persisted user (defense in depth).
    if str(user.organization_id) != claims.get("org"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "org mismatch")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def load_project(session: AsyncSession, user: User, project_id: uuid.UUID) -> Project:
    """Fetch an org-scoped project or raise 404. Shared by the project routers."""
    try:
        return await project_service.get_project(session, user.organization_id, project_id)
    except project_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found") from exc


def actor_from_user(user: User) -> Actor:
    return Actor(
        actor_type=ActorType.USER,
        organization_id=user.organization_id,
        user_id=user.id,
        system_role=user.system_role,
    )


def require(action: Action):
    """Dependency factory: 403 unless the current user may perform ``action``.

    Project-plane checks (which need a project_id from the path) are added in
    Phase 3; this guards the system plane for Phase 2 endpoints.
    """

    async def _guard(user: CurrentUser) -> User:
        if not authorize(actor_from_user(user), action):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"not permitted: {action.value}")
        return user

    return _guard
