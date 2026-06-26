"""Tasks, dependencies (cycle-checked), Kanban transitions, and timeline/CPM."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import DependencyType, KanbanColumn
from app.core.roles import ActorType
from app.models.project import Project
from app.models.task import Task, TaskDependency
from app.scheduling.critical_path import Edge, TaskNode, compute_critical_path
from app.scheduling.graph import CycleError, DependencyGraph


class DependencyCycle(Exception):
    """Raised when adding a dependency would create a cycle."""

    def __init__(self, cycle: list[uuid.UUID]):
        self.cycle = cycle
        super().__init__("dependency would create a cycle")


class DuplicateDependency(Exception):
    pass


class TaskNotFound(Exception):
    pass


async def create_task(
    session: AsyncSession,
    *,
    project: Project,
    title: str,
    description: str,
    estimate_hours: float,
    required_capabilities: list | None,
    is_human_task: bool,
    milestone_id: uuid.UUID | None,
    priority: int,
) -> Task:
    task = Task(
        organization_id=project.organization_id,
        project_id=project.id,
        title=title,
        description=description,
        estimate_hours=estimate_hours,
        required_capabilities=required_capabilities,
        is_human_task=is_human_task,
        milestone_id=milestone_id,
        priority=priority,
    )
    session.add(task)
    await session.flush()
    return task


async def list_tasks(session: AsyncSession, project_id: uuid.UUID) -> list[Task]:
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.order_index)
    return list((await session.execute(stmt)).scalars().all())


async def _dependencies(session: AsyncSession, project_id: uuid.UUID) -> list[TaskDependency]:
    stmt = select(TaskDependency).where(TaskDependency.project_id == project_id)
    return list((await session.execute(stmt)).scalars().all())


async def add_dependency(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID,
    predecessor_id: uuid.UUID,
    successor_id: uuid.UUID,
    dependency_type: DependencyType,
    lag_hours: float,
) -> TaskDependency:
    """Create a dependency, rejecting self-loops, duplicates, and cycles."""
    if predecessor_id == successor_id:
        raise DependencyCycle([predecessor_id, successor_id])

    # Both tasks must belong to this project.
    tasks = await list_tasks(session, project.id)
    ids = {t.id for t in tasks}
    if predecessor_id not in ids or successor_id not in ids:
        raise TaskNotFound()

    existing = await _dependencies(session, project.id)
    for dep in existing:
        if dep.predecessor_task_id == predecessor_id and dep.successor_task_id == successor_id:
            raise DuplicateDependency()

    # Build the current graph + the proposed edge, then check for a cycle.
    graph: DependencyGraph[uuid.UUID] = DependencyGraph()
    for t in tasks:
        graph.add_node(t.id)
    for dep in existing:
        graph.add_edge(dep.predecessor_task_id, dep.successor_task_id)
    try:
        graph.add_edge(predecessor_id, successor_id)
        cycle = graph.find_cycle()
    except CycleError as exc:
        raise DependencyCycle(exc.cycle) from exc
    if cycle is not None:
        raise DependencyCycle(cycle)

    dependency = TaskDependency(
        organization_id=project.organization_id,
        project_id=project.id,
        predecessor_task_id=predecessor_id,
        successor_task_id=successor_id,
        dependency_type=dependency_type,
        lag_hours=lag_hours,
    )
    session.add(dependency)
    await record_audit(
        session,
        organization_id=project.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="dependency.added",
        entity_type="TaskDependency",
        entity_id=None,
        after={"predecessor": str(predecessor_id), "successor": str(successor_id)},
    )
    return dependency


async def set_kanban_column(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID,
    task_id: uuid.UUID,
    column: KanbanColumn,
) -> Task:
    task = await session.get(Task, task_id)
    if task is None or task.project_id != project.id:
        raise TaskNotFound()
    before = task.kanban_column.value
    task.kanban_column = column
    await record_audit(
        session,
        organization_id=project.organization_id,
        actor_type=ActorType.USER,
        actor_id=actor_id,
        action="task.kanban_moved",
        entity_type="Task",
        entity_id=task.id,
        before={"kanban_column": before},
        after={"kanban_column": column.value},
    )
    return task


@dataclass(frozen=True)
class TaskSchedule:
    task_id: uuid.UUID
    earliest_start: float
    earliest_finish: float
    latest_start: float
    latest_finish: float
    slack: float
    is_critical: bool


@dataclass(frozen=True)
class Timeline:
    project_duration: float
    critical_path: list[uuid.UUID]
    schedules: list[TaskSchedule]


async def compute_timeline(session: AsyncSession, project_id: uuid.UUID) -> Timeline:
    """Compute the CPM timeline for a project from its tasks + dependencies."""
    tasks = await list_tasks(session, project_id)
    deps = await _dependencies(session, project_id)

    nodes = [TaskNode(id=t.id, duration=t.estimate_hours) for t in tasks]
    edges = [
        Edge(predecessor=d.predecessor_task_id, successor=d.successor_task_id, lag=d.lag_hours)
        for d in deps
    ]
    result = compute_critical_path(nodes, edges)  # raises CycleError if corrupt

    schedules = [
        TaskSchedule(
            task_id=tid,
            earliest_start=s.earliest_start,
            earliest_finish=s.earliest_finish,
            latest_start=s.latest_start,
            latest_finish=s.latest_finish,
            slack=s.slack,
            is_critical=s.is_critical,
        )
        for tid, s in result.schedules.items()
    ]
    return Timeline(
        project_duration=result.project_duration,
        critical_path=result.critical_path,
        schedules=schedules,
    )


async def dependency_edges(session: AsyncSession, project_id: uuid.UUID) -> list[TaskDependency]:
    """Expose dependencies for the graph view."""
    return await _dependencies(session, project_id)
