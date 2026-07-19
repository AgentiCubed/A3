"""Analytics & reporting: dashboard, metric materialization, exports."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession, require
from app.core.audit import record_audit
from app.core.rbac import Action
from app.core.roles import ActorType
from app.models.user import User
from app.schemas.artifact import ArtifactResponse
from app.schemas.project import ProjectCloseRequest
from app.services import (
    acceptance_service,
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


@router.get("/{project_id}/acceptance")
async def acceptance_report(project_id: uuid.UUID, session: DbSession, user: CurrentUser) -> dict:
    """Live acceptance-criteria status — what still stands between here and closed."""
    project = await _project(session, user, project_id)
    report = await acceptance_service.evaluate_project_acceptance(session, project=project)
    return report.to_dict()


@router.post("/{project_id}/close")
async def close_project(
    project_id: uuid.UUID,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.PROJECT_EDIT))],
    req: ProjectCloseRequest | None = None,
) -> dict:
    """Close the project — refused while acceptance criteria fail (WS-4b).

    A 409 lists the unmet criteria. Passing acknowledge_unmet_criteria=true
    closes a legacy manual project anyway (deliberate abandonment) and records
    the acknowledgment. Approved-plan projects cannot waive their gates.
    """
    project = await _project(session, user, project_id)
    try:
        close_result = await closeout_service.close_project(
            session,
            project=project,
            actor_id=user.id,
            acknowledge_unmet_criteria=bool(req and req.acknowledge_unmet_criteria),
        )
    except closeout_service.GovernedPlanApprovalRequired as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "plan_approval_required"},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "plan_approval_required"},
        ) from exc
    except closeout_service.GovernedMaterializationInvalid as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "approved_materialization_invalid", "detail": exc.reason},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "approved_materialization_invalid", "reason": exc.reason},
        ) from exc
    except closeout_service.GovernedProjectNotActive as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "governed_project_not_active"},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "governed_project_not_active"},
        ) from exc
    except closeout_service.PlanTasksIncomplete as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "plan_tasks_incomplete", "tasks": exc.tasks},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "plan_tasks_incomplete", "tasks": exc.tasks},
        ) from exc
    except closeout_service.PlanTaskEvidenceInvalid as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "plan_task_evidence_invalid", "tasks": exc.tasks},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "plan_task_evidence_invalid", "tasks": exc.tasks},
        ) from exc
    except closeout_service.AcceptanceNotMet as exc:
        # Persist the refusal before answering: the audit trail must show the
        # gate firing even though the request fails.
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.close_refused",
            entity_type="Project",
            entity_id=project.id,
            after={
                "reason": "acceptance_criteria_unmet",
                "unmet_criteria": [r.key for r in exc.report.unmet],
                "acknowledgement_allowed": exc.acknowledgement_allowed,
            },
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {
                "error": "acceptance_criteria_unmet",
                "unmet": [r.to_dict() for r in exc.report.unmet],
                "acknowledgement_allowed": exc.acknowledgement_allowed,
                "hint": (
                    "resolve the criteria or pass acknowledge_unmet_criteria=true"
                    if exc.acknowledgement_allowed
                    else "resolve every criterion; governed acceptance cannot be waived"
                ),
            },
        ) from exc
    report = await closeout_service.generate_closeout(
        session,
        org_id=user.organization_id,
        project_id=project_id,
        generated_at=datetime.now(UTC),
        acceptance=close_result.acceptance,
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
