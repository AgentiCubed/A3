"""Project, methodology, requirements, milestones."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import (
    Methodology,
    MilestoneStatus,
    ProjectStatus,
    RecommendedBy,
    RequirementKind,
    RequirementPriority,
)
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(
            "acceptance_revision >= 0",
            name="ck_projects_acceptance_revision_nonnegative",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
        default=ProjectStatus.INTAKE,
    )
    acceptance_criteria: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    acceptance_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    closure_acceptance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ProjectMethodology(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_methodologies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    methodology: Mapped[Methodology] = mapped_column(
        Enum(
            Methodology,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
    )
    recommended_by: Mapped[RecommendedBy] = mapped_column(
        Enum(
            RecommendedBy,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=RecommendedBy.SYSTEM,
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ProjectRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "project_requirements"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[RequirementKind] = mapped_column(
        Enum(
            RequirementKind,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(
            RequirementPriority,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=10,
        ),
        nullable=False,
        default=RequirementPriority.SHOULD,
    )
    source: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Milestone(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "milestones"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(
            MilestoneStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=MilestoneStatus.OPEN,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
