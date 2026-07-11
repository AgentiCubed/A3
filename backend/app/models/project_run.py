"""ProjectRun — a resumable orchestration run over all tasks in a project."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ProjectRunStatus
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_runs"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    initiated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[ProjectRunStatus] = mapped_column(
        Enum(
            ProjectRunStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=ProjectRunStatus.RUNNING,
    )
