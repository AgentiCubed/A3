"""User and ProjectMember (the two RBAC role planes)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.roles import ProjectRole, SystemRole
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_user_org_email"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    system_role: Mapped[SystemRole] = mapped_column(
        Enum(
            SystemRole, native_enum=False, values_callable=lambda o: [e.value for e in o], length=20
        ),
        nullable=False,
        default=SystemRole.MEMBER,
    )


class ProjectMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Project-plane role grant (the RBAC project plane). FK to projects added in
    Phase 3 now that the projects table exists."""

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_member_project_user"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_role: Mapped[ProjectRole] = mapped_column(
        Enum(
            ProjectRole,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=20,
        ),
        nullable=False,
    )
