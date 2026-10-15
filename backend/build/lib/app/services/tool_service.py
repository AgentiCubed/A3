"""Tool registry and least-privilege agent-tool permissions.

Default-deny: an AgentToolPermission row's existence IS the permission. The grant
path carries the three-layer anti-self-escalation block (security-model §5):
RBAC at the API, a service guard here, and an audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import ToolKind, ToolSensitivity
from app.core.rbac import Actor
from app.core.roles import ActorType
from app.db.queries import list_by_org
from app.models.agent import AgentToolPermission, Tool
from app.services.errors import NotFound


class SelfEscalation(Exception):
    """An agent attempted to grant or alter a tool permission."""


class DuplicatePermission(Exception):
    pass


async def register_tool(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    kind: ToolKind,
    description: str,
    schema: dict | None,
    sensitivity: ToolSensitivity,
) -> Tool:
    tool = Tool(
        organization_id=org_id,
        name=name,
        kind=kind,
        description=description,
        schema=schema,
        sensitivity=sensitivity,
    )
    session.add(tool)
    await session.flush()
    await record_audit(
        session,
        organization_id=org_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="tool.registered",
        entity_type="Tool",
        entity_id=tool.id,
        after={"name": name, "sensitivity": sensitivity.value},
    )
    return tool


async def list_tools(session: AsyncSession, org_id: uuid.UUID) -> list[Tool]:
    return await list_by_org(session, Tool, org_id)


async def grant_tool_permission(
    session: AsyncSession,
    *,
    actor: Actor,
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
    scope: dict | None,
    expires_at: datetime | None,
) -> AgentToolPermission:
    """Grant (agent, tool). Agents can never grant permissions (self-escalation)."""
    # Layer 2: service guard. (Layer 1 is the API RBAC guard; layer 3 is audit.)
    if actor.actor_type != ActorType.USER:
        raise SelfEscalation("only users may grant tool permissions")

    existing = (
        await session.execute(
            select(AgentToolPermission).where(
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.tool_id == tool_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise DuplicatePermission()

    perm = AgentToolPermission(
        organization_id=actor.organization_id,
        agent_id=agent_id,
        tool_id=tool_id,
        scope=scope,
        granted_by=actor.user_id,
        expires_at=expires_at,
    )
    session.add(perm)
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor.user_id,
        action="tool_permission.granted",
        entity_type="AgentToolPermission",
        entity_id=None,
        after={"agent_id": str(agent_id), "tool_id": str(tool_id), "scope": scope},
    )
    return perm


async def revoke_tool_permission(
    session: AsyncSession, *, actor: Actor, agent_id: uuid.UUID, tool_id: uuid.UUID
) -> None:
    if actor.actor_type != ActorType.USER:
        raise SelfEscalation("only users may revoke tool permissions")
    perm = (
        await session.execute(
            select(AgentToolPermission).where(
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.tool_id == tool_id,
            )
        )
    ).scalar_one_or_none()
    if perm is None:
        raise NotFound("permission")
    await session.delete(perm)
    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor.user_id,
        action="tool_permission.revoked",
        entity_type="AgentToolPermission",
        entity_id=perm.id,
        before={"agent_id": str(agent_id), "tool_id": str(tool_id)},
    )


async def has_permission(
    session: AsyncSession,
    *,
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
    now: datetime,
) -> bool:
    """Default-deny check used at tool-invocation time (Phase 5+)."""
    perm = (
        await session.execute(
            select(AgentToolPermission).where(
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.tool_id == tool_id,
            )
        )
    ).scalar_one_or_none()
    if perm is None:
        return False
    if perm.expires_at is not None and perm.expires_at <= now:
        return False
    return True


async def list_permissions(
    session: AsyncSession, *, org_id: uuid.UUID, agent_id: uuid.UUID
) -> list[AgentToolPermission]:
    return await list_by_org(
        session, AgentToolPermission, org_id, AgentToolPermission.agent_id == agent_id
    )
