"""Agent registry, capabilities, tool registry, tool permissions, matching."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, actor_from_user, require
from app.core.rbac import Action
from app.models.user import User
from app.orchestration.adapters.registry import UnknownProvider
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    CapabilityCreate,
    CapabilityResponse,
    MatchResponse,
    PermissionGrant,
    PermissionResponse,
    ToolCreate,
    ToolResponse,
)
from app.services import agent_service, tool_service

router = APIRouter(tags=["agents"])

AgentManager = Annotated[User, Depends(require(Action.AGENT_MANAGE))]
ToolManager = Annotated[User, Depends(require(Action.TOOL_MANAGE))]
PermissionGranter = Annotated[User, Depends(require(Action.TOOL_PERMISSION_GRANT))]


# ── Agents ────────────────────────────────────────────────────────────────
@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(req: AgentCreate, session: DbSession, user: AgentManager):
    try:
        agent = await agent_service.register_agent(
            session,
            org_id=user.organization_id,
            actor_id=user.id,
            name=req.name,
            kind=req.kind,
            provider=req.provider,
            model=req.model,
            default_role=req.default_role,
            config=req.config,
        )
    except UnknownProvider as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown provider: {exc}"
        ) from exc
    await session.commit()
    return AgentResponse.model_validate(agent)


@router.get("/agents", response_model=list[AgentResponse])
async def list_agents(session: DbSession, user: CurrentUser):
    rows = await agent_service.list_agents(session, user.organization_id)
    return [AgentResponse.model_validate(a) for a in rows]


@router.post(
    "/agents/{agent_id}/capabilities",
    response_model=CapabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_capability(
    agent_id: uuid.UUID, req: CapabilityCreate, session: DbSession, user: AgentManager
):
    try:
        agent = await agent_service.get_agent(session, user.organization_id, agent_id)
    except agent_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from exc
    try:
        cap = await agent_service.add_capability(
            session,
            agent=agent,
            capability=req.capability,
            proficiency=req.proficiency,
            evidence=req.evidence,
        )
    except agent_service.UnknownCapability as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"error": "unknown_capability", "keys": exc.keys},
        ) from exc
    await session.commit()
    return CapabilityResponse.model_validate(cap)


@router.get("/agents/matches", response_model=list[MatchResponse])
async def match_agents(
    session: DbSession,
    user: CurrentUser,
    capability: Annotated[list[str], Query(default_factory=list)],
):
    results = await agent_service.match_for_capabilities(
        session, user.organization_id, list(capability)
    )
    return [
        MatchResponse(
            agent_id=r.agent_id,
            name=r.name,
            eligible=r.eligible,
            coverage=r.coverage,
            matched=r.matched,
            missing=r.missing,
            score=r.score,
        )
        for r in results
    ]


# ── Tools ─────────────────────────────────────────────────────────────────
@router.post("/tools", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def register_tool(req: ToolCreate, session: DbSession, user: ToolManager):
    tool = await tool_service.register_tool(
        session,
        org_id=user.organization_id,
        actor_id=user.id,
        name=req.name,
        kind=req.kind,
        description=req.description,
        schema=req.schema_,
        sensitivity=req.sensitivity,
    )
    await session.commit()
    return ToolResponse.model_validate(tool)


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(session: DbSession, user: CurrentUser):
    rows = await tool_service.list_tools(session, user.organization_id)
    return [ToolResponse.model_validate(t) for t in rows]


# ── Tool permissions (least-privilege, default-deny) ──────────────────────
@router.post(
    "/agents/{agent_id}/tools/{tool_id}/permission",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_permission(
    agent_id: uuid.UUID,
    tool_id: uuid.UUID,
    req: PermissionGrant,
    session: DbSession,
    user: PermissionGranter,
):
    # Verify both belong to the caller's org before granting.
    try:
        await agent_service.get_agent(session, user.organization_id, agent_id)
    except agent_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from exc
    tools = {t.id for t in await tool_service.list_tools(session, user.organization_id)}
    if tool_id not in tools:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tool not found")

    try:
        perm = await tool_service.grant_tool_permission(
            session,
            actor=actor_from_user(user),
            agent_id=agent_id,
            tool_id=tool_id,
            scope=req.scope,
            expires_at=req.expires_at,
        )
    except tool_service.DuplicatePermission as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "permission already granted") from exc
    await session.commit()
    return PermissionResponse.model_validate(perm)


@router.delete(
    "/agents/{agent_id}/tools/{tool_id}/permission", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_permission(
    agent_id: uuid.UUID, tool_id: uuid.UUID, session: DbSession, user: PermissionGranter
):
    try:
        await tool_service.revoke_tool_permission(
            session, actor=actor_from_user(user), agent_id=agent_id, tool_id=tool_id
        )
    except tool_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "permission not found") from exc
    await session.commit()


@router.get("/agents/{agent_id}/permissions", response_model=list[PermissionResponse])
async def list_permissions(agent_id: uuid.UUID, session: DbSession, user: CurrentUser):
    rows = await tool_service.list_permissions(
        session, org_id=user.organization_id, agent_id=agent_id
    )
    return [PermissionResponse.model_validate(p) for p in rows]
