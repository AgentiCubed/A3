"""plan materialization and evaluation provenance

Revision ID: 0010_plan_materialization
Revises: 0009_decomposition_plans
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_plan_materialization"
down_revision: str | None = "0009_decomposition_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("evaluator_agent_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("acceptance_criteria", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    )
    op.add_column(
        "tasks",
        sa.Column("max_remediations", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("tasks", sa.Column("source_plan_id", sa.Uuid(), nullable=True))
    op.add_column("tasks", sa.Column("source_plan_task_key", sa.String(80), nullable=True))
    op.create_foreign_key(
        "fk_tasks_evaluator_agent_id_agents",
        "tasks",
        "agents",
        ["evaluator_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tasks_source_plan_id_decomposition_plans",
        "tasks",
        "decomposition_plans",
        ["source_plan_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_tasks_max_remediations",
        "tasks",
        "max_remediations >= 0 AND max_remediations <= 5",
    )
    op.create_check_constraint(
        "ck_tasks_source_plan_pair",
        "tasks",
        "(source_plan_id IS NULL AND source_plan_task_key IS NULL) OR "
        "(source_plan_id IS NOT NULL AND source_plan_task_key IS NOT NULL)",
    )
    op.create_unique_constraint(
        "uq_task_source_plan_key", "tasks", ["source_plan_id", "source_plan_task_key"]
    )
    op.create_index("ix_tasks_source_plan_id", "tasks", ["source_plan_id"])

    op.add_column(
        "evaluations",
        sa.Column("rubric_specs", sa.JSON(), nullable=True),
    )
    op.add_column(
        "evaluations",
        sa.Column("rubric_sha256", sa.String(64), nullable=True),
    )
    op.add_column("evaluations", sa.Column("rubric_source", sa.String(24), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluations", "rubric_source")
    op.drop_column("evaluations", "rubric_sha256")
    op.drop_column("evaluations", "rubric_specs")
    op.drop_index("ix_tasks_source_plan_id", table_name="tasks")
    op.drop_constraint("uq_task_source_plan_key", "tasks", type_="unique")
    op.drop_constraint("ck_tasks_source_plan_pair", "tasks", type_="check")
    op.drop_constraint("ck_tasks_max_remediations", "tasks", type_="check")
    op.drop_constraint("fk_tasks_source_plan_id_decomposition_plans", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_evaluator_agent_id_agents", "tasks", type_="foreignkey")
    op.drop_column("tasks", "source_plan_task_key")
    op.drop_column("tasks", "source_plan_id")
    op.drop_column("tasks", "max_remediations")
    op.drop_column("tasks", "acceptance_criteria")
    op.drop_column("tasks", "evaluator_agent_id")
