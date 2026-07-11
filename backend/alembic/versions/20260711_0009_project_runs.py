"""project_runs

Revision ID: 0009_project_runs
Revises: 0008_artifacts
Create Date: 2026-07-11

Resumable project-run orchestration table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_project_runs"
down_revision: str | None = "0008_artifacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RUN_STATUS = ("running", "completed", "cancelled")


def upgrade() -> None:
    op.create_table(
        "project_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "initiated_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                *_RUN_STATUS,
                name="project_run_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
            server_default="running",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_project_runs_project", "project_runs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_runs_project", table_name="project_runs")
    op.drop_table("project_runs")
