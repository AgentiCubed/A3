"""decomposition plans

Revision ID: 0009_decomposition_plans
Revises: 0008_artifacts
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_decomposition_plans"
down_revision: str | None = "0008_artifacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "decomposition_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Uuid(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "planner_agent_id",
            sa.Uuid(),
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contract_version", sa.String(40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("objective_sha256", sa.String(64), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("plan_spec", sa.JSON(), nullable=True),
        sa.Column("plan_spec_sha256", sa.String(64), nullable=True),
        sa.Column("provider_output_sha256", sa.String(64), nullable=True),
        sa.Column("provider_output_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("diagnostic", sa.String(500), nullable=True),
        sa.Column(
            "decided_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft', 'invalid', 'approved', 'rejected')",
            name="ck_decomposition_plans_status",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_decomposition_plans_organization_id", "decomposition_plans", ["organization_id"]
    )
    op.create_index("ix_decomposition_plans_project_id", "decomposition_plans", ["project_id"])
    op.create_index(
        "uq_decomposition_plans_project_version",
        "decomposition_plans",
        ["project_id", "version"],
        unique=True,
    )
    op.create_index(
        "uq_decomposition_plans_active_draft",
        "decomposition_plans",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("status = 'draft'"),
        sqlite_where=sa.text("status = 'draft'"),
    )


def downgrade() -> None:
    op.drop_table("decomposition_plans")
