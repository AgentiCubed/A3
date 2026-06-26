"""Evaluation and EvaluationCriterion (both immutable)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import EvaluatorKind, Verdict
from app.db.base import Base, Immutable, UUIDPrimaryKeyMixin


class Evaluation(UUIDPrimaryKeyMixin, Immutable, Base):
    """Append-only verdict on one TaskExecution's output."""

    __tablename__ = "evaluations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("task_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Null for deterministic/human; set (and != executor) for agent evaluators.
    evaluator_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    evaluator_kind: Mapped[EvaluatorKind] = mapped_column(
        Enum(
            EvaluatorKind,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=16,
        ),
        nullable=False,
    )
    verdict: Mapped[Verdict] = mapped_column(
        Enum(Verdict, native_enum=False, values_callable=lambda o: [e.value for e in o], length=16),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    gaps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EvaluationCriterion(UUIDPrimaryKeyMixin, Immutable, Base):
    """Append-only per-criterion result within an Evaluation."""

    __tablename__ = "evaluation_criteria"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
