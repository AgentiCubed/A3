"""TaskExecution — an immutable record of one execution attempt."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, Immutable, UUIDPrimaryKeyMixin
from app.orchestration.state_machine.states import ExecutionState


class TaskExecution(UUIDPrimaryKeyMixin, Immutable, Base):
    """Append-only. One row per attempt; never updated or deleted."""

    __tablename__ = "task_executions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Terminal state snapshot for this attempt (COMPLETED or FAILED).
    state: Mapped[ExecutionState] = mapped_column(
        Enum(ExecutionState, native_enum=False, length=20), nullable=False
    )
    # Secret-free context that was sent to the agent.
    input_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_handle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Links this attempt to the prior execution it remediates (Phase 6).
    remediation_of: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("task_executions.id", ondelete="SET NULL"), nullable=True
    )
