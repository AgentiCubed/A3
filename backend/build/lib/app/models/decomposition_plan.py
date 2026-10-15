"""Durable objective-to-plan proposal awaiting an explicit human decision."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import DecompositionPlanStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DecompositionPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decomposition_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'invalid', 'approved', 'rejected')",
            name="ck_decomposition_plans_status",
        ),
        Index(
            "uq_decomposition_plans_project_version",
            "project_id",
            "version",
            unique=True,
        ),
        Index(
            "uq_decomposition_plans_active_draft",
            "project_id",
            unique=True,
            postgresql_where=text("status = 'draft'"),
            sqlite_where=text("status = 'draft'"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    planner_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    contract_version: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    objective_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[DecompositionPlanStatus] = mapped_column(
        Enum(
            DecompositionPlanStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=DecompositionPlanStatus.DRAFT,
    )
    plan_spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    plan_spec_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_output_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_output_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    diagnostic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
