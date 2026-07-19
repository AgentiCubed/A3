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

from app.api.deps import CurrentUser, DbSession, actor_from_user, require
from app.core.audit import record_audit
from app.core.rbac import Action
from app.core.roles import ActorType
from app.models.project import (
    Milestone,
    Project,
    ProjectMethodology,
    ProjectRequirement,
)
from app.models.risk import Decision, Risk
from app.models.user import User
from app.orchestration.engines import get_workflow_engine
from app.orchestration.state_machine.machine import IllegalTransition
from app.orchestration.state_machine.states import ExecutionState
from app.schemas.agent import AssignRequest
from app.schemas.approval import ApprovalDecision, ApprovalResponse
from app.schemas.execution import (
    DispatchAcceptedResponse,
    DispatchRequest,
    DispatchResultResponse,
    EvaluationResponse,
    ExecutionResponse,
    ProjectStartRequest,
    ProjectStartResponse,
    ReassignRequest,
    StartedTaskResponse,
)
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
from app.services import (
    acceptance_boundary_service,
    agent_service,
    approval_service,
    decomposition_service,
    evaluation_service,
    execution_service,
    project_service,
    scheduler_service,
    task_service,
)
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
        acceptance_criteria=(
            req.acceptance_criteria.model_dump(exclude_none=True)
            if req.acceptance_criteria
            else None
        ),
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
    try:
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
    except task_service.GovernedGraphLocked as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.graph_mutation_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": "approved_plan_graph_locked", "mutation": "task.create"},
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "approved_plan_graph_locked"},
        ) from exc
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


@router.patch("/{project_id}/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task_agent(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    req: AssignRequest,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.AGENT_ASSIGN))],
):
    project = await _load_project(session, user, project_id)
    tasks = await task_service.list_tasks(session, project.id)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    try:
        agent = await agent_service.get_agent(session, user.organization_id, req.agent_id)
    except agent_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from exc
    try:
        task = await agent_service.assign_agent_to_task(
            session, org_id=user.organization_id, actor_id=user.id, task=task, agent=agent
        )
    except agent_service.CapabilityMismatch as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"error": "capability_mismatch", "missing": exc.missing},
        ) from exc
    except agent_service.GovernedAssignmentLocked as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "plan-derived task assignment requires a new governed plan decision",
        ) from exc
    await session.commit()
    return TaskResponse.model_validate(task)


# ── Execution (start, dispatch, history, reassignment) ────────────────────
@router.post("/{project_id}/start", response_model=ProjectStartResponse)
async def start_project(
    project_id: uuid.UUID,
    req: ProjectStartRequest,
    session: DbSession,
    user: TaskEditor,
):
    """Start the project's execution loop: dispatch every dependency-satisfied task.

    Celery mode queues the initial wave and returns immediately; the worker
    dispatches successors as their predecessors complete. Inline mode runs the
    whole dependency chain in-request. Unassigned, human, and
    dependency-blocked tasks are left untouched and keep gating their
    successors.
    """
    project = await _load_project(session, user, project_id)

    async def audit_refusal(reason: str, **details: object) -> None:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.start_refused",
            entity_type="Project",
            entity_id=project.id,
            after={"reason": reason, **details},
        )
        await session.commit()

    try:
        materialization = await decomposition_service.begin_project_execution(
            session,
            project=project,
            actor_id=user.id,
        )
    except decomposition_service.PlanApprovalRequired as exc:
        await audit_refusal("plan_approval_required")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "plan_approval_required"},
        ) from exc
    except decomposition_service.MaterializationInvalid as exc:
        await audit_refusal("approved_materialization_invalid", detail=exc.reason)
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "approved_materialization_invalid", "reason": exc.reason},
        ) from exc
    except decomposition_service.GovernedProjectNotStartable as exc:
        await audit_refusal("governed_project_not_startable")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "governed_project_not_startable"},
        ) from exc

    if materialization is None:
        # Preserve the pre-WS-6 manual-project behavior and audit shape.
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.started",
            entity_type="Project",
            entity_id=project.id,
        )
    else:
        # Make ACTIVE + project.started durable before any broker, provider,
        # evaluator, or tool can produce external effects.
        await session.commit()
    engine = get_workflow_engine()
    if engine is not None:
        params = execution_service.build_dispatch_params(
            actor_id=user.id,
            actor_type=ActorType.USER,
            max_attempts=req.max_attempts,
            timeout_s=req.timeout_s,
            evaluation=None,
        )
        outcomes = await scheduler_service.dispatch_ready(
            session,
            project_id=project.id,
            engine=engine,
            params=params,
            actor_id=user.id,
            actor_type=ActorType.USER,
        )
        await session.commit()
        return ProjectStartResponse(
            engine=engine.name,
            tasks=[StartedTaskResponse(task_id=o.task_id, status=o.status) for o in outcomes],
        )

    try:
        outcomes = await scheduler_service.run_inline(
            session,
            project_id=project.id,
            actor_id=user.id,
            actor_type=ActorType.USER,
            max_attempts=req.max_attempts,
            timeout_s=req.timeout_s,
        )
    except execution_service.ProjectClosed as exc:
        await session.rollback()
        await audit_refusal("project_closed")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "project_closed"},
        ) from exc
    await session.commit()
    return ProjectStartResponse(
        engine="inline",
        tasks=[StartedTaskResponse(task_id=o.task_id, status=o.status) for o in outcomes],
    )


@router.post(
    "/{project_id}/tasks/{task_id}/dispatch",
    response_model=DispatchResultResponse | DispatchAcceptedResponse,
)
async def dispatch_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    req: DispatchRequest,
    session: DbSession,
    user: TaskEditor,
):
    """Dispatch a task to its assigned agent.

    With WORKFLOW_ENGINE_BACKEND=celery (compose/prod) the task is queued
    through the WorkflowEngine port and this returns immediately with
    DispatchAcceptedResponse — the worker executes it. In inline mode
    (dev/tests) execution runs in-request and the full result is returned.
    """
    project = await _load_project(session, user, project_id)
    tasks = await task_service.list_tasks(session, project.id)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    refusal_scope = (
        user.organization_id,
        user.id,
        project.id,
        task.id,
        task.source_plan_id,
    )

    async def audit_dispatch_refusal(reason: str) -> None:
        organization_id, actor_id, persisted_project_id, persisted_task_id, source_plan_id = (
            refusal_scope
        )
        # A failed late evidence claim may leave ORM task transitions pending.
        # Discard them before retaining the refusal as the only durable change.
        await session.rollback()
        details = {"reason": reason}
        if source_plan_id is not None:
            details["source_plan_id"] = str(source_plan_id)
        await record_audit(
            session,
            organization_id=organization_id,
            project_id=persisted_project_id,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            action="task.dispatch_refused",
            entity_type="Task",
            entity_id=persisted_task_id,
            after=details,
        )
        await session.commit()

    evaluation_cfg = None
    if req.rubric is not None or req.evaluator_agent_id is not None:
        if req.evaluator_agent_id is not None and req.evaluator_agent_id == task.assigned_agent_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "evaluator agent must differ from the executor (executor/evaluator separation)",
            )
        evaluation_cfg = execution_service.EvaluationConfig(
            rubric_specs=[
                criterion.model_dump(mode="json", exclude_none=True)
                for criterion in (req.rubric or [])
            ],
            evaluator_agent_id=req.evaluator_agent_id,
            max_remediations=req.max_remediations,
        )

    engine = get_workflow_engine()
    if engine is not None:
        try:
            await execution_service.queue_task(
                session,
                task=task,
                actor_id=user.id,
                actor_type=ActorType.USER,
                evaluation=evaluation_cfg,
            )
        except execution_service.AlreadyQueued as exc:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "task is already queued; re-dispatch would run it twice",
            ) from exc
        except execution_service.NotAssigned as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "task has no assigned agent"
            ) from exc
        except execution_service.NotExecutable as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "assigned agent is not currently eligible to execute",
            ) from exc
        except execution_service.EvaluationConfigConflict as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        except execution_service.ProjectClosed as exc:
            await audit_dispatch_refusal("project_closed")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {"error": "project_closed"},
            ) from exc
        except execution_service.GovernedProjectNotActive as exc:
            await audit_dispatch_refusal("governed_project_not_active")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {"error": "governed_project_not_active"},
            ) from exc
        except execution_service.GovernedDependenciesIncomplete as exc:
            await audit_dispatch_refusal("governed_dependencies_incomplete")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {"error": "governed_dependencies_incomplete"},
            ) from exc
        except IllegalTransition as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        # Commit BEFORE submitting so the worker sees the QUEUED state.
        await session.commit()
        params = execution_service.build_dispatch_params(
            actor_id=user.id,
            actor_type=ActorType.USER,
            max_attempts=req.max_attempts,
            timeout_s=req.timeout_s,
            evaluation=evaluation_cfg,
        )
        try:
            # Hold the same project boundary across the quick broker publish so
            # a message cannot be created after closure has already committed.
            await acceptance_boundary_service.lock_acceptance_for_close(
                session,
                project_id=project.id,
                org_id=user.organization_id,
            )
        except acceptance_boundary_service.ProjectClosed as exc:
            await audit_dispatch_refusal("project_closed")
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                {"error": "project_closed"},
            ) from exc
        try:
            handle = engine.submit_execution(task.id, params)
        except Exception as exc:  # noqa: BLE001 - broker down/unreachable
            # The QUEUED commit already happened but no message exists; park the
            # task in BLOCKED (re-dispatchable) instead of leaving it stuck.
            await execution_service.transition_task(
                session,
                task,
                ExecutionState.BLOCKED,
                actor_id=user.id,
                actor_type=ActorType.USER,
                reason=f"engine submit failed: {type(exc).__name__}",
            )
            await session.commit()
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "task queueing failed; task moved to BLOCKED for re-dispatch",
            ) from exc
        await session.commit()
        return DispatchAcceptedResponse(
            task_id=task.id,
            status=task.status,
            engine=engine.name,
            engine_handle=handle,
        )

    try:
        result = await execution_service.execute_task(
            session,
            task=task,
            actor_id=user.id,
            actor_type=ActorType.USER,
            max_attempts=req.max_attempts,
            timeout_s=req.timeout_s,
            evaluation=evaluation_cfg,
        )
    except execution_service.NotAssigned as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "task has no assigned agent"
        ) from exc
    except execution_service.NotExecutable as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "assigned agent is not currently eligible to execute",
        ) from exc
    except execution_service.EvaluationConfigConflict as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except execution_service.ProjectClosed as exc:
        await audit_dispatch_refusal("project_closed")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "project_closed"},
        ) from exc
    except execution_service.GovernedProjectNotActive as exc:
        await audit_dispatch_refusal("governed_project_not_active")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "governed_project_not_active"},
        ) from exc
    except execution_service.GovernedDependenciesIncomplete as exc:
        await audit_dispatch_refusal("governed_dependencies_incomplete")
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "governed_dependencies_incomplete"},
        ) from exc
    except evaluation_service.EvaluatorConflict as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "evaluator agent must differ from the executor (executor/evaluator separation)",
        ) from exc
    except IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    await session.commit()
    return DispatchResultResponse(
        final_state=result.final_state,
        attempts=result.attempts,
        escalated=result.escalated,
        output=result.output,
        execution_ids=result.execution_ids,
        verdict=result.verdict,
        remediations=result.remediations,
    )


@router.get("/{project_id}/tasks/{task_id}/executions", response_model=list[ExecutionResponse])
async def list_executions(
    project_id: uuid.UUID, task_id: uuid.UUID, session: DbSession, user: CurrentUser
):
    await _load_project(session, user, project_id)
    rows = await execution_service.list_executions(
        session, org_id=user.organization_id, task_id=task_id
    )
    return [ExecutionResponse.model_validate(r) for r in rows]


@router.get("/{project_id}/tasks/{task_id}/evaluations", response_model=list[EvaluationResponse])
async def list_task_evaluations(
    project_id: uuid.UUID, task_id: uuid.UUID, session: DbSession, user: CurrentUser
):
    await _load_project(session, user, project_id)
    rows = await evaluation_service.list_evaluations_for_task(
        session, org_id=user.organization_id, task_id=task_id
    )
    return [EvaluationResponse.model_validate(r) for r in rows]


# ── Approvals ─────────────────────────────────────────────────────────────
@router.get("/{project_id}/approvals", response_model=list[ApprovalResponse])
async def list_approvals(project_id: uuid.UUID, session: DbSession, user: CurrentUser):
    project = await _load_project(session, user, project_id)
    rows = await approval_service.list_approvals(
        session, org_id=user.organization_id, project_id=project.id
    )
    return [ApprovalResponse.model_validate(a) for a in rows]


@router.post("/{project_id}/approvals/{approval_id}/decide", response_model=ApprovalResponse)
async def decide_approval(
    project_id: uuid.UUID,
    approval_id: uuid.UUID,
    req: ApprovalDecision,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.APPROVAL_DECIDE))],
):
    await _load_project(session, user, project_id)
    try:
        approval = await approval_service.decide_approval(
            session,
            actor=actor_from_user(user),
            approval_id=approval_id,
            approve=req.approve,
            comment=req.comment,
        )
    except approval_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "approval not found") from exc
    except approval_service.AlreadyDecided as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "approval already decided") from exc
    await session.commit()
    return ApprovalResponse.model_validate(approval)


@router.patch("/{project_id}/tasks/{task_id}/reassign", response_model=TaskResponse)
async def reassign_task(
    project_id: uuid.UUID,
    task_id: uuid.UUID,
    req: ReassignRequest,
    session: DbSession,
    user: Annotated[User, Depends(require(Action.AGENT_ASSIGN))],
):
    project = await _load_project(session, user, project_id)
    tasks = await task_service.list_tasks(session, project.id)
    task = next((t for t in tasks if t.id == task_id), None)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "task not found")
    try:
        agent = await agent_service.get_agent(session, user.organization_id, req.agent_id)
    except agent_service.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from exc

    missing = await agent_service.missing_capabilities(
        session, user.organization_id, agent.id, list(task.required_capabilities or [])
    )
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"error": "capability_mismatch", "missing": missing},
        )
    try:
        await execution_service.reassign_task(
            session, task=task, new_agent=agent, actor_id=user.id, actor_type=ActorType.USER
        )
    except execution_service.GovernedAssignmentLocked as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "plan-derived task assignment requires a new governed plan decision",
        ) from exc
    except IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
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
    except task_service.GovernedGraphLocked as exc:
        await record_audit(
            session,
            organization_id=user.organization_id,
            project_id=project.id,
            actor_type=ActorType.USER,
            actor_id=user.id,
            action="project.graph_mutation_refused",
            entity_type="Project",
            entity_id=project.id,
            after={
                "reason": "approved_plan_graph_locked",
                "mutation": "dependency.create",
            },
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            {"error": "approved_plan_graph_locked"},
        ) from exc
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
