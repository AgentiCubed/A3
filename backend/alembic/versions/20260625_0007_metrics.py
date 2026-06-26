"""project & agent metrics

Revision ID: 0007_metrics
Revises: 0006_evaluations_approvals
Create Date: 2026-06-25

Phase 7. Materialized metric snapshots for dashboards and exports.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_metrics"
down_revision: Union[str, None] = "0006_evaluations_approvals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(60), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_project_metrics_org", "project_metrics", ["organization_id"])
    op.create_index("ix_project_metrics_project", "project_metrics", ["project_id"])
    op.create_index("ix_project_metrics_metric", "project_metrics", ["metric"])

    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric", sa.String(60), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=True),
        sa.Column("as_of", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_metrics_org", "agent_metrics", ["organization_id"])
    op.create_index("ix_agent_metrics_agent", "agent_metrics", ["agent_id"])
    op.create_index("ix_agent_metrics_metric", "agent_metrics", ["metric"])


def downgrade() -> None:
    op.drop_table("agent_metrics")
    op.drop_table("project_metrics")
