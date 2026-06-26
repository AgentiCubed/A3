"""Task, dependency, kanban, timeline, and graph schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.enums import DependencyType, KanbanColumn
from app.orchestration.state_machine.states import ExecutionState


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    estimate_hours: float = Field(default=0.0, ge=0)
    required_capabilities: list[str] | None = None
    is_human_task: bool = False
    milestone_id: uuid.UUID | None = None
    priority: int = Field(default=3, ge=1, le=5)


class TaskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    status: ExecutionState
    kanban_column: KanbanColumn
    estimate_hours: float
    required_capabilities: list[str] | None
    is_human_task: bool
    milestone_id: uuid.UUID | None
    priority: int

    model_config = {"from_attributes": True}


class KanbanUpdate(BaseModel):
    kanban_column: KanbanColumn


class DependencyCreate(BaseModel):
    predecessor_task_id: uuid.UUID
    successor_task_id: uuid.UUID
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_hours: float = 0.0


class DependencyResponse(BaseModel):
    id: uuid.UUID
    predecessor_task_id: uuid.UUID
    successor_task_id: uuid.UUID
    dependency_type: DependencyType
    lag_hours: float

    model_config = {"from_attributes": True}


class TaskScheduleResponse(BaseModel):
    task_id: uuid.UUID
    earliest_start: float
    earliest_finish: float
    latest_start: float
    latest_finish: float
    slack: float
    is_critical: bool


class TimelineResponse(BaseModel):
    project_duration: float
    critical_path: list[uuid.UUID]
    schedules: list[TaskScheduleResponse]


class GraphNode(BaseModel):
    id: uuid.UUID
    title: str
    is_critical: bool = False


class GraphEdge(BaseModel):
    predecessor_task_id: uuid.UUID
    successor_task_id: uuid.UUID
    dependency_type: DependencyType
    lag_hours: float


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
