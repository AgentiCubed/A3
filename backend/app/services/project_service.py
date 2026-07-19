"""Project, methodology, requirements, milestones, risks, decisions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import ProjectStatus
from app.core.roles import ActorType
from app.models.project import (
    Milestone,
    Project,
    ProjectMethodology,
    ProjectRequirement,
)
from app.models.risk import Decision, Risk
from app.services.methodology import ProjectSignals, recommend_methodology


class NotFound(Exception):
    pass


class AlreadyHalted(Exception):
    """Halt requested on a project that is already halted."""


class NotHalted(Exception):
    """Resume requested on a project that is not halted."""


class ProjectClosedError(Exception):
    """Halt/resume requested on a CLOSED project (nothing left to control)."""


async def halt_project(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
    reason: str | None = None,
) -> Project:
    """Operator halt: the scheduler dispatches nothing new for this project.

    In-flight tasks conclude cleanly; the halt only closes the intake of new
    work. Audited, reversible via ``resume_project``.
    """
    if project.status == ProjectStatus.CLOSED:
        raise ProjectClosedError()
    if project.halted_at is not None:
        raise AlreadyHalted()
    project.halted_at = datetime.now(UTC)
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="project.halted",
        entity_type="Project",
        entity_id=project.id,
        after={"halted_at": project.halted_at.isoformat(), "reason": reason},
    )
    return project


async def resume_project(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
) -> Project:
    """Lift an operator halt. The caller decides whether to re-kick dispatch."""
    if project.status == ProjectStatus.CLOSED:
        raise ProjectClosedError()
    if project.halted_at is None:
        raise NotHalted()
    halted_since = project.halted_at.isoformat()
    project.halted_at = None
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="project.resumed",
        entity_type="Project",
        entity_id=project.id,
        before={"halted_at": halted_since},
        after={"halted_at": None},
    )
    return project


async def get_project(session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = await session.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise NotFound("project")
    return project


async def create_project(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    objective: str,
    acceptance_criteria: dict | None,
    signals: ProjectSignals | None,
) -> tuple[Project, ProjectMethodology]:
    project = Project(
        organization_id=org_id,
        name=name,
        objective=objective,
        acceptance_criteria=acceptance_criteria,
        created_by=actor_id,
    )
    session.add(project)
    await session.flush()

    rec = recommend_methodology(signals or _default_signals())
    methodology = ProjectMethodology(
        organization_id=org_id,
        project_id=project.id,
        methodology=rec.methodology,
        rationale=rec.rationale,
        config=rec.config,
    )
    session.add(methodology)

    await record_audit(
        session,
        organization_id=org_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="project.created",
        entity_type="Project",
        entity_id=project.id,
        after={"name": name, "methodology": rec.methodology.value},
    )
    return project, methodology


def _default_signals() -> ProjectSignals:
    # Neutral defaults → Scrum/Hybrid; callers should pass real signals.
    return ProjectSignals(
        requirements_stable=False,
        hard_deadline=False,
        many_dependencies=False,
        continuous_flow=False,
        resource_constrained=False,
    )


async def add_requirement(
    session: AsyncSession, *, project: Project, kind, text: str, priority, source: str | None
) -> ProjectRequirement:
    req = ProjectRequirement(
        organization_id=project.organization_id,
        project_id=project.id,
        kind=kind,
        text=text,
        priority=priority,
        source=source,
    )
    session.add(req)
    return req


async def add_milestone(
    session: AsyncSession, *, project: Project, name: str, due_date, order_index: int
) -> Milestone:
    milestone = Milestone(
        organization_id=project.organization_id,
        project_id=project.id,
        name=name,
        due_date=due_date,
        order_index=order_index,
    )
    session.add(milestone)
    return milestone


async def add_risk(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID,
    title: str,
    description: str,
    likelihood: int,
    impact: int,
    mitigation: str | None,
) -> Risk:
    risk = Risk(
        organization_id=project.organization_id,
        project_id=project.id,
        title=title,
        description=description,
        likelihood=likelihood,
        impact=impact,
        severity=likelihood * impact,
        mitigation=mitigation,
    )
    session.add(risk)
    await record_audit(
        session,
        organization_id=project.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="risk.created",
        entity_type="Risk",
        entity_id=None,
        after={"title": title, "severity": likelihood * impact},
    )
    return risk


async def add_decision(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID,
    title: str,
    context: str,
    decision: str,
    consequences: str,
) -> Decision:
    row = Decision(
        organization_id=project.organization_id,
        project_id=project.id,
        title=title,
        context=context,
        decision=decision,
        consequences=consequences,
        decided_by=actor_id,
    )
    session.add(row)
    await record_audit(
        session,
        organization_id=project.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="decision.recorded",
        entity_type="Decision",
        entity_id=None,
        after={"title": title},
    )
    return row


async def list_project_children(session: AsyncSession, model, project_id: uuid.UUID) -> list:
    stmt = select(model).where(model.project_id == project_id)
    return list((await session.execute(stmt)).scalars().all())
