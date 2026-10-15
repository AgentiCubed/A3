"""Organization membership management (system-role plane).

Demonstrates org-scoped reads, the USER_MANAGE guard, and audited mutations.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, require
from app.core.audit import record_audit
from app.core.rbac import Action
from app.core.roles import ActorType
from app.db.repository import OrgScopedRepository
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.org import RoleUpdateRequest

router = APIRouter(prefix="/orgs", tags=["orgs"])


class UserRepository(OrgScopedRepository[User]):
    model = User


@router.get("/me/members", response_model=list[UserResponse])
async def list_members(user: CurrentUser, session: DbSession) -> list[UserResponse]:
    repo = UserRepository(session, user.organization_id)
    members = await repo.list()
    return [UserResponse.model_validate(m) for m in members]


@router.patch("/me/members/{user_id}/role", response_model=UserResponse)
async def set_member_role(
    user_id: uuid.UUID,
    req: RoleUpdateRequest,
    session: DbSession,
    actor: Annotated[User, Depends(require(Action.USER_MANAGE))],
) -> UserResponse:
    repo = UserRepository(session, actor.organization_id)
    target = await repo.get(user_id)  # org-scoped: cross-org returns None
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")

    before = {"system_role": target.system_role.value}
    target.system_role = req.system_role
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor.id,
        action="user.role_changed",
        entity_type="User",
        entity_id=target.id,
        before=before,
        after={"system_role": req.system_role.value},
    )
    await session.commit()
    return UserResponse.model_validate(target)
