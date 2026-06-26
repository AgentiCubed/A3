"""Projects and planning: requirements, milestones, tasks, dependencies,
Kanban, timeline (CPM), dependency graph, risks, decisions.

Reads require authentication; mutations go through the system-plane RBAC guard.
Project-plane role resolution is a Phase-4+ refinement (assumption A18).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require
from app.core.rbac import Action
from app.models.project import (
    Milestone,
    Project,
    ProjectMethodology,
    ProjectRequirement,
)
from app.models.risk import Decision, Risk
from app.models.user import User
from app.schemas.project import (
    MethodologyResponse,
    MilestoneCreate,
    MilestoneResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectWithMethodology,
    RequirementCreate,
    RequirementResponse,
)
from app.schemas.risk import (
    DecisionCreate,
    DecisionResponse,
    RiskCreate,
    RiskResponse,
)
from app.schemas.task import (
    DependencyCreate,
    DependencyResponse,
    GraphEdge,
    GraphNode,
    GraphResponse,
    KanbanUpdate,
    TaskCreate,
    TaskResponse,
    TaskScheduleResponse,
    TimelineResponse,
)
from app.services import project_service, task_service
from app.services.methodology import ProjectSignals

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectEditor = Annotated[User, Depends(require(Action.PROJECT_EDIT))]
ProjectCreator = Annotated[User, Depends(require(Action.PROJECT_CREATE))]
TaskEditor = Annotated[User, Depends(require(Action.TASK_EDIT))]


async def _load_project(session, user: User, project_id: uuid.UUID):
    try:
        return await project_service.get_project(session, user.organization_id, project_id)
    except project_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found") from exc


# ── Projects ──────────────────────────────────────────────────────────────
@router.post("", response_model=ProjectWithMethodology, status_code=status.HTTP_201_CREATED)
async def create_project(req: ProjectCreate, session: DbSession, user: ProjectCreator):
    signals = ProjectSignals(**req.signals.model_dump()) if req.signals else None
    project, methodology = await project_service.create_project(
        session,
        org_id=user.organization_id,
        actor_id=user.id,
        name=req.name,
        objective=req.objective,
        acceptance_criteria=req.acceptance_criteria,
        signals=signals,
    )
    await session.commit()
    out = ProjectWithMethodology.model_validate(project)
    out.methodology = MethodologyResponse.model_validate(methodology)
    return out


@router.get("", response_model=list[ProjectResponse])
async def list_projects(session: DbSession, user: CurrentUser):
    stmt = select(Project).where(Project.organization_id == user.organization_id)
    rows = (await session.execute(stmt)).scalars().all()
    return [ProjectResponse.model_validate(p) for p in rows]


@router.get("/{project_id}", response_model=ProjectWithMethodology)
async def get_project(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    out = ProjectWithMethodology.model_validate(project)
    meth = (
        await session.execute(
            select(ProjectMethodology).where(ProjectMethodology.project_id == project.id)
        )
    ).scalar_one_or_none()
    if meth is not None:
        out.methodology = MethodologyResponse.model_validate(meth)
    return out


# ── Requirements ──────────────────────────────────────────────────────────
@router.post(
    "/{project_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_requirement(
    project_id: uuid.UUID, req: RequirementCreate, session: DbSession, user: ProjectEditor
):
    project = await _load_project(session, user, project_id)
    row = await project_service.add_requirement(
        session,
        project=project,
        kind=req.kind,
        text=req.text,
        priority=req.priority,
        source=req.source,
    )
    await session.commit()
    return RequirementResponse.model_validate(row)


@router.get("/{project_id}/requirements", response_model=list[RequirementResponse])
async def list_requirements(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await project_service.list_project_children(session, ProjectRequirement, project.id)
    return [RequirementResponse.model_validate(r) for r in rows]


# ── Milestones ────────────────────────────────────────────────────────────
@router.post(
    "/{project_id}/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_milestone(
    project_id: uuid.UUID, req: MilestoneCreate, session: DbSession, user: ProjectEditor
):
    project = await _load_project(session, user, project_id)
    row = await project_service.add_milestone(
        session, project=project, name=req.name, due_date=req.due_date, order_index=req.order_index
    )
    await session.commit()
    return MilestoneResponse.model_validate(row)


@router.get("/{project_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await project_service.list_project_children(session, Milestone, project.id)
    return [MilestoneResponse.model_validate(r) for r in rows]


# ── Tasks ─────────────────────────────────────────────────────────────────
@router.post(
    "/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED
)
async def add_task(project_id: uuid.UUID, req: TaskCreate, session: DbSession, user: TaskEditor):
    project = await _load_project(session, user, project_id)
    task = await task_service.create_task(
        session,
        project=project,
        title=req.title,
        description=req.description,
        estimate_hours=req.estimate_hours,
        required_capabilities=req.required_capabilities,
        is_human_task=req.is_human_task,
        milestone_id=req.milestone_id,
        priority=req.priority,
    )
    await session.commit()
    return TaskResponse.model_validate(task)


@router.get("/{project_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await task_service.list_tasks(session, project.id)
    return [TaskResponse.model_validate(t) for t in rows]


@router.patch("/{project_id}/tasks/{task_id}/kanban", response_model=TaskResponse)
async def move_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    req: KanbanUpdate,
    session: DbSession,
    user: TaskEditor,
):
    project = await _load_project(session, user, project_id)
    try:
        task = await task_service.set_kanban_column(
            session, project=project, actor_id=user.id, task_id=task_id, column=req.kanban_column
        )
    except task_service.TaskNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found") from exc
    await session.commit()
    return TaskResponse.model_validate(task)


# ── Dependencies ──────────────────────────────────────────────────────────
@router.post(
    "/{project_id}/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_dependency(
    project_id: uuid.UUID, req: DependencyCreate, session: DbSession, user: TaskEditor
):
    project = await _load_project(session, user, project_id)
    try:
        dep = await task_service.add_dependency(
            session,
            project=project,
            actor_id=user.id,
            predecessor_id=req.predecessor_task_id,
            successor_id=req.successor_task_id,
            dependency_type=req.dependency_type,
            lag_hours=req.lag_hours,
        )
    except task_service.DependencyCycle as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "dependency_cycle", "cycle": [str(n) for n in exc.cycle]},
        ) from exc
    except task_service.DuplicateDependency as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "dependency already exists") from exc
    except task_service.TaskNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not in project") from exc
    await session.commit()
    return DependencyResponse.model_validate(dep)


# ── Timeline (CPM) + dependency graph ─────────────────────────────────────
@router.get("/{project_id}/timeline", response_model=TimelineResponse)
async def get_timeline(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    timeline = await task_service.compute_timeline(session, project.id)
    return TimelineResponse(
        project_duration=timeline.project_duration,
        critical_path=timeline.critical_path,
        schedules=[TaskScheduleResponse(**vars(s)) for s in timeline.schedules],
    )


@router.get("/{project_id}/graph", response_model=GraphResponse)
async def get_graph(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    tasks = await task_service.list_tasks(session, project.id)
    edges = await task_service.dependency_edges(session, project.id)
    timeline = await task_service.compute_timeline(session, project.id)
    critical = set(timeline.critical_path)
    return GraphResponse(
        nodes=[GraphNode(id=t.id, title=t.title, is_critical=t.id in critical) for t in tasks],
        edges=[
            GraphEdge(
                predecessor_task_id=e.predecessor_task_id,
                successor_task_id=e.successor_task_id,
                dependency_type=e.dependency_type,
                lag_hours=e.lag_hours,
            )
            for e in edges
        ],
    )


# ── Risks & decisions ─────────────────────────────────────────────────────
@router.post(
    "/{project_id}/risks", response_model=RiskResponse, status_code=status.HTTP_201_CREATED
)
async def add_risk(project_id: uuid.UUID, req: RiskCreate, session: DbSession, user: ProjectEditor):
    project = await _load_project(session, user, project_id)
    row = await project_service.add_risk(
        session,
        project=project,
        actor_id=user.id,
        title=req.title,
        description=req.description,
        likelihood=req.likelihood,
        impact=req.impact,
        mitigation=req.mitigation,
    )
    await session.commit()
    return RiskResponse.model_validate(row)


@router.get("/{project_id}/risks", response_model=list[RiskResponse])
async def list_risks(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await project_service.list_project_children(session, Risk, project.id)
    return [RiskResponse.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/decisions",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_decision(
    project_id: uuid.UUID, req: DecisionCreate, session: DbSession, user: ProjectEditor
):
    project = await _load_project(session, user, project_id)
    row = await project_service.add_decision(
        session,
        project=project,
        actor_id=user.id,
        title=req.title,
        context=req.context,
        decision=req.decision,
        consequences=req.consequences,
    )
    await session.commit()
    return DecisionResponse.model_validate(row)


@router.get("/{project_id}/decisions", response_model=list[DecisionResponse])
async def list_decisions(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await project_service.list_project_children(session, Decision, project.id)
    return [DecisionResponse.model_validate(r) for r in rows]
