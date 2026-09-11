"""Agent registry, capabilities, tools, tool permissions, prompt templates."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.enums import (
    AgentKind,
    AgentRole,
    AgentStatus,
    PromptRole,
    ToolKind,
    ToolSensitivity,
)
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[AgentKind] = mapped_column(
        Enum(
            AgentKind, native_enum=False, values_callable=lambda o: [e.value for e in o], length=10
        ),
        nullable=False,
        default=AgentKind.AI,
    )
    provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(
            AgentStatus,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=12,
        ),
        nullable=False,
        default=AgentStatus.ACTIVE,
    )
    default_role: Mapped[AgentRole] = mapped_column(
        Enum(
            AgentRole, native_enum=False, values_callable=lambda o: [e.value for e in o], length=12
        ),
        nullable=False,
        default=AgentRole.EITHER,
    )
    # No secrets here — credentials referenced by env key (e.g. {"api_key_ref": "..."}).
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AgentCapability(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_capabilities"
    __table_args__ = (UniqueConstraint("agent_id", "capability", name="uq_agent_capability"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability: Mapped[str] = mapped_column(String(80), nullable=False)
    proficiency: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)


class Tool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tools"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[ToolKind] = mapped_column(
        Enum(
            ToolKind, native_enum=False, values_callable=lambda o: [e.value for e in o], length=16
        ),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sensitivity: Mapped[ToolSensitivity] = mapped_column(
        Enum(
            ToolSensitivity,
            native_enum=False,
            values_callable=lambda o: [e.value for e in o],
            length=10,
        ),
        nullable=False,
        default=ToolSensitivity.LOW,
    )


class AgentToolPermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Default-deny grant: a row's existence is the permission. No row = denied."""

    __tablename__ = "agent_tool_permissions"
    __table_args__ = (UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool_permission"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PromptTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    role: Mapped[PromptRole] = mapped_column(
        Enum(
            PromptRole, native_enum=False, values_callable=lambda o: [e.value for e in o], length=12
        ),
        nullable=False,
    )
    template: Mapped[str] = mapped_column(Text, nullable=False)
    input_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
