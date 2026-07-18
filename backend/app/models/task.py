"""Task and TaskDependency."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import DependencyType, KanbanColumn
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.orchestration.state_machine.states import ExecutionState


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("source_plan_id", "source_plan_task_key", name="uq_task_source_plan_key"),
        CheckConstraint(
            "(source_plan_id IS NULL AND source_plan_task_key IS NULL) OR "
            "(source_plan_id IS NOT NULL AND source_plan_task_key IS NOT NULL)",
            name="ck_tasks_source_plan_pair",
        ),
        CheckConstraint(
            "max_remediations >= 0 AND max_remediations <= 5",
            name="ck_tasks_max_remediations",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[ExecutionState] = mapped_column(
        Enum(
            ExecutionState,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
        default=ExecutionState.PLANNED,
    )
    kanban_column: Mapped[KanbanColumn] = mapped_column(
        Enum(
            KanbanColumn,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=KanbanColumn.BACKLOG,
    )
    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    evaluator_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    required_capabilities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    max_remediations: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("decomposition_plans.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    source_plan_task_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    estimate_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_human_task: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wbs_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TaskDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "predecessor_task_id", "successor_task_id", name="uq_dependency_pred_succ"
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    predecessor_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    successor_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(
            DependencyType,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
        default=DependencyType.FINISH_TO_START,
    )
    lag_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
