"""Approval — a human gate before irreversible/sensitive actions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ApprovalStatus, RiskLevel
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approvals"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("task_executions.id", ondelete="SET NULL"), nullable=True
    )
    requested_action: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(
            RiskLevel, native_enum=False, values_callable=lambda o: [e.value for e in o], length=10
        ),
        nullable=False,
        default=RiskLevel.MEDIUM,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(
            ApprovalStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
