"""atomic project close acceptance boundary

Revision ID: 0011_atomic_project_close
Revises: 0010_plan_materialization
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_atomic_project_close"
down_revision: str | None = "0010_plan_materialization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("acceptance_revision", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("projects", sa.Column("closure_acceptance", sa.JSON(), nullable=True))
    op.create_check_constraint(
        "ck_projects_acceptance_revision_nonnegative",
        "projects",
        "acceptance_revision >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_projects_acceptance_revision_nonnegative",
        "projects",
        type_="check",
    )
    op.drop_column("projects", "closure_acceptance")
    op.drop_column("projects", "acceptance_revision")
