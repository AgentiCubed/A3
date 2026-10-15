"""ProjectMetric and AgentMetric — materialized analytics snapshots."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, UUIDPrimaryKeyMixin


class ProjectMetric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "project_metrics"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AgentMetric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_metrics"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
