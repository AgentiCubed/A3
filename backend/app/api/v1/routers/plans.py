"""Objective-to-plan draft endpoints (WS-6)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession, require
from app.core.enums import DecompositionPlanStatus
from app.core.rbac import Action
from app.models.user import User
from app.schemas.decomposition import (
    DecompositionPlanResponse,
    PlanGenerateRequest,
    PlanRejectRequest,
)
from app.services import decomposition_service, project_service

router = APIRouter(prefix="/projects/{project_id}/plans", tags=["plans"])

ProjectEditor = Annotated[User, Depends(require(Action.PROJECT_EDIT))]
PlanApprover = Annotated[User, Depends(require(Action.APPROVAL_DECIDE))]


async def _project(session: DbSession, user: User, project_id: uuid.UUID):
    try:
        return await project_service.get_project(session, user.organization_id, project_id)
    except project_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found") from exc


@router.post("", response_model=DecompositionPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    project_id: uuid.UUID,
    req: PlanGenerateRequest,
    session: DbSession,
    user: ProjectEditor,
):
    project = await _project(session, user, project_id)
    try:
        plan = await decomposition_service.generate_plan(
            session,
            project=project,
            planner_agent_id=req.planner_agent_id,
            actor_id=user.id,
        )
    except decomposition_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except decomposition_service.PlannerUnavailable as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "planner unavailable") from exc
    except decomposition_service.ActiveDraftExists as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "an active draft already exists") from exc
    except decomposition_service.ProjectNotPlannable as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "project status does not permit plan generation"
        ) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "an active draft already exists") from exc
    if plan.status == DecompositionPlanStatus.INVALID:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "error": "plan_generation_failed",
                "plan_id": str(plan.id),
                "code": plan.error_code,
                "detail": plan.diagnostic,
            },
        )
    return DecompositionPlanResponse.model_validate(plan)


@router.get("", response_model=list[DecompositionPlanResponse])
async def list_plans(
    project_id: uuid.UUID,
    session: DbSession,
    user: CurrentUser,
):
    project = await _project(session, user, project_id)
    plans = await decomposition_service.list_plans(session, project=project)
    return [DecompositionPlanResponse.model_validate(plan) for plan in plans]


@router.get("/{plan_id}", response_model=DecompositionPlanResponse)
async def get_plan(
    project_id: uuid.UUID,
    plan_id: uuid.UUID,
    session: DbSession,
    user: CurrentUser,
):
    project = await _project(session, user, project_id)
    try:
        plan = await decomposition_service.get_plan(session, project=project, plan_id=plan_id)
    except decomposition_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "plan not found") from exc
    return DecompositionPlanResponse.model_validate(plan)


@router.post("/{plan_id}/reject", response_model=DecompositionPlanResponse)
async def reject_plan(
    project_id: uuid.UUID,
    plan_id: uuid.UUID,
    req: PlanRejectRequest,
    session: DbSession,
    user: PlanApprover,
):
    project = await _project(session, user, project_id)
    try:
        plan = await decomposition_service.reject_plan(
            session,
            project=project,
            plan_id=plan_id,
            actor_id=user.id,
            comment=req.comment,
        )
    except decomposition_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "plan not found") from exc
    except decomposition_service.AlreadyDecided as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "plan already decided") from exc
    await session.flush()
    await session.refresh(plan)
    response = DecompositionPlanResponse.model_validate(plan)
    await session.commit()
    return response
