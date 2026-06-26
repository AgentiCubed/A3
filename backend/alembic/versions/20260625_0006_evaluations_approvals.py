"""evaluations, criteria (immutable), approvals

Revision ID: 0006_evaluations_approvals
Revises: 0005_task_executions
Create Date: 2026-06-25

Phase 6. Append-only evaluations + evaluation_criteria (Postgres triggers reuse
the block function from 0002) and the approvals gate.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_evaluations_approvals"
down_revision: Union[str, None] = "0005_task_executions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EVALUATOR_KIND = ("deterministic", "agent", "human")
_VERDICT = ("pass", "fail", "needs_revision")
_RISK_LEVEL = ("low", "medium", "high")
_APPROVAL_STATUS = ("pending", "approved", "rejected")


def _enum(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def _ts(col: str) -> sa.Column:
    return sa.Column(col, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "task_execution_id", sa.Uuid(), sa.ForeignKey("task_executions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("evaluator_agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evaluator_kind", _enum("evaluator_kind", _EVALUATOR_KIND), nullable=False),
        sa.Column("verdict", _enum("verdict", _VERDICT), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("gaps", sa.JSON(), nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_evaluations_org", "evaluations", ["organization_id"])
    op.create_index("ix_evaluations_execution", "evaluations", ["task_execution_id"])

    op.create_table(
        "evaluation_criteria",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "evaluation_id", sa.Uuid(), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("criterion", sa.String(80), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        _ts("created_at"),
    )
    op.create_index("ix_eval_criteria_org", "evaluation_criteria", ["organization_id"])
    op.create_index("ix_eval_criteria_eval", "evaluation_criteria", ["evaluation_id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "task_execution_id", sa.Uuid(), sa.ForeignKey("task_executions.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("requested_action", sa.Text(), nullable=False),
        sa.Column("risk_level", _enum("risk_level", _RISK_LEVEL), nullable=False),
        sa.Column("status", _enum("approval_status", _APPROVAL_STATUS), nullable=False),
        sa.Column("decided_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_approvals_org", "approvals", ["organization_id"])
    op.create_index("ix_approvals_project", "approvals", ["project_id"])

    if op.get_bind().dialect.name == "postgresql":
        for table in ("evaluations", "evaluation_criteria"):
            op.execute(
                f"""
                CREATE TRIGGER trg_{table}_immutable
                BEFORE UPDATE OR DELETE ON {table}
                FOR EACH ROW EXECUTE FUNCTION agenticubed_block_mutation();
                """
            )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in ("evaluations", "evaluation_criteria"):
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_immutable ON {table};")
    op.drop_table("approvals")
    op.drop_table("evaluation_criteria")
    op.drop_table("evaluations")
