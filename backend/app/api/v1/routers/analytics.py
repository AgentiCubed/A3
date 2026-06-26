"""Analytics & reporting: dashboard, metric materialization, exports."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession, require
from app.core.rbac import Action
from app.models.user import User
from app.schemas.artifact import ArtifactResponse
from app.services import (
    analytics_service,
    artifact_service,
    closeout_service,
    export_service,
    project_service,
)

router = APIRouter(prefix="/projects", tags=["analytics"])


async def _project(session, user: User, project_id: uuid.UUID):
    try:
        return await project_service.get_project(session, user.organization_id, project_id)
    except project_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found") from exc


@router.get("/{project_id}/dashboard")
async def dashboard(project_id: uuid.UUID, session: DbSession, user: CurrentUser) -> dict:
    await _project(session, user, project_id)
    return await analytics_service.project_dashboard(
        session, org_id=user.organization_id, project_id=project_id
    )


@router.post("/{project_id}/metrics/recompute")
async def recompute_metrics(
    project_id: uuid.UUID,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.PROJECT_EDIT))],
) -> dict:
    await _project(session, user, project_id)
    result = await analytics_service.materialize_metrics(
        session, org_id=user.organization_id, project_id=project_id
    )
    await session.commit()
    return result


@router.get("/{project_id}/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    await _project(session, user, project_id)
    rows = await artifact_service.list_artifacts(
        session, org_id=user.organization_id, project_id=project_id
    )
    return [ArtifactResponse.model_validate(a) for a in rows]


@router.get("/{project_id}/closeout")
async def closeout(project_id: uuid.UUID, session: DbSession, user: CurrentUser) -> dict:
    await _project(session, user, project_id)
    return await closeout_service.generate_closeout(
        session,
        org_id=user.organization_id,
        project_id=project_id,
        generated_at=datetime.now(UTC),
    )


@router.post("/{project_id}/close")
async def close_project(
    project_id: uuid.UUID,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.PROJECT_EDIT))],
) -> dict:
    project = await _project(session, user, project_id)
    await closeout_service.close_project(session, project=project, actor_id=user.id)
    report = await closeout_service.generate_closeout(
        session, org_id=user.organization_id, project_id=project_id, generated_at=datetime.now(UTC)
    )
    await session.commit()
    return {"status": project.status.value, "closeout": report}


@router.get("/{project_id}/export.json")
async def export_json(project_id: uuid.UUID, session: DbSession, user: CurrentUser) -> Response:
    await _project(session, user, project_id)
    payload = await export_service.project_json(
        session, org_id=user.organization_id, project_id=project_id
    )
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"content-disposition": f'attachment; filename="project-{project_id}.json"'},
    )


@router.get("/{project_id}/export/tasks.csv")
async def export_tasks_csv(
    project_id: uuid.UUID, session: DbSession, user: CurrentUser
) -> Response:
    await _project(session, user, project_id)
    csv_text = await export_service.tasks_csv(session, project_id=project_id)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"content-disposition": f'attachment; filename="tasks-{project_id}.csv"'},
    )


@router.get("/{project_id}/export/powerbi.zip")
async def export_powerbi(project_id: uuid.UUID, session: DbSession, user: CurrentUser) -> Response:
    await _project(session, user, project_id)
    data = await export_service.powerbi_zip(
        session, org_id=user.organization_id, project_id=project_id
    )
    return Response(
        content=data,
        media_type="application/zip",
        headers={"content-disposition": f'attachment; filename="powerbi-{project_id}.zip"'},
    )
