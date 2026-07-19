"""persist provider request receipt

Revision ID: 0013_provider_request_receipt
Revises: 0012_project_halt
Create Date: 2026-07-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_provider_request_receipt"
down_revision: str | None = "0012_project_halt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "task_executions",
        sa.Column("provider_request_id", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task_executions", "provider_request_id")
