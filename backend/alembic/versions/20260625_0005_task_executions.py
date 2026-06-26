"""task executions (immutable)

Revision ID: 0005_task_executions
Revises: 0004_agents_tools
Create Date: 2026-06-25

Phase 5. Append-only task_executions (one row per attempt). A Postgres trigger
(reusing the function from 0002) blocks UPDATE/DELETE for defense-in-depth; the
application enforces immutability too.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_task_executions"
down_revision: Union[str, None] = "0004_agents_tools"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EXEC_STATE = (
    "planned",
    "ready",
    "queued",
    "running",
    "evaluating",
    "awaiting_approval",
    "completed",
    "failed",
    "blocked",
    "cancelled",
)


def upgrade() -> None:
    op.create_table(
        "task_executions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "state",
            sa.Enum(*_EXEC_STATE, name="task_execution_state", native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("input_context", sa.JSON(), nullable=True),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_estimate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(60), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("workflow_handle", sa.String(120), nullable=True),
        sa.Column(
            "remediation_of",
            sa.Uuid(),
            sa.ForeignKey("task_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_task_executions_org", "task_executions", ["organization_id"])
    op.create_index("ix_task_executions_task", "task_executions", ["task_id"])

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE TRIGGER trg_task_executions_immutable
            BEFORE UPDATE OR DELETE ON task_executions
            FOR EACH ROW EXECUTE FUNCTION agenticubed_block_mutation();
            """
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_task_executions_immutable ON task_executions;")
    op.drop_table("task_executions")
