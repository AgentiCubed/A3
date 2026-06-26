"""projects & planning domain

Revision ID: 0003_projects_planning
Revises: 0002_auth_orgs_audit
Create Date: 2026-06-25

Phase 3. Projects, methodology, requirements, milestones, tasks, dependencies,
risks, decisions. Also adds the deferred project_members.project_id FK now that
the projects table exists (assumption A17 resolved).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_projects_planning"
down_revision: Union[str, None] = "0002_auth_orgs_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PROJECT_STATUS = ("intake", "planning", "active", "blocked", "closed")
_METHODOLOGY = ("kanban", "scrum", "waterfall", "cpm", "ccpm", "hybrid")
_RECOMMENDED_BY = ("system", "user")
_REQ_KIND = ("functional", "nonfunctional", "constraint", "acceptance")
_REQ_PRIORITY = ("must", "should", "could", "wont")
_MILESTONE_STATUS = ("open", "reached", "missed")
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
_KANBAN = ("backlog", "ready", "in_progress", "review", "done")
_DEP_TYPE = ("finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish")
_RISK_STATUS = ("open", "mitigating", "closed")


def _enum(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def _ts(col: str) -> sa.Column:
    return sa.Column(col, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def _org_fk() -> sa.Column:
    return sa.Column(
        "organization_id",
        sa.Uuid(),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )


def _project_fk(unique: bool = False) -> sa.Column:
    return sa.Column(
        "project_id",
        sa.Uuid(),
        sa.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=unique,
    )


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", _enum("project_status", _PROJECT_STATUS), nullable=False),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    op.create_table(
        "project_methodologies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(unique=True),
        sa.Column("methodology", _enum("methodology", _METHODOLOGY), nullable=False),
        sa.Column("recommended_by", _enum("recommended_by", _RECOMMENDED_BY), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("config", sa.JSON(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_methodologies_org", "project_methodologies", ["organization_id"])
    op.create_index("ix_methodologies_project", "project_methodologies", ["project_id"])

    op.create_table(
        "project_requirements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("kind", _enum("requirement_kind", _REQ_KIND), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("priority", _enum("requirement_priority", _REQ_PRIORITY), nullable=False),
        sa.Column("source", sa.String(200), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_requirements_org", "project_requirements", ["organization_id"])
    op.create_index("ix_requirements_project", "project_requirements", ["project_id"])

    op.create_table(
        "milestones",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", _enum("milestone_status", _MILESTONE_STATUS), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_milestones_org", "milestones", ["organization_id"])
    op.create_index("ix_milestones_project", "milestones", ["project_id"])

    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("milestone_id", sa.Uuid(), sa.ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", _enum("execution_state", _EXEC_STATE), nullable=False),
        sa.Column("kanban_column", _enum("kanban_column", _KANBAN), nullable=False),
        sa.Column("assigned_agent_id", sa.Uuid(), nullable=True),
        sa.Column("required_capabilities", sa.JSON(), nullable=True),
        sa.Column("estimate_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_human_task", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("wbs_code", sa.String(40), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_tasks_org", "tasks", ["organization_id"])
    op.create_index("ix_tasks_project", "tasks", ["project_id"])
    op.create_index("ix_tasks_milestone", "tasks", ["milestone_id"])

    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("predecessor_task_id", sa.Uuid(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("successor_task_id", sa.Uuid(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dependency_type", _enum("dependency_type", _DEP_TYPE), nullable=False),
        sa.Column("lag_hours", sa.Float(), nullable=False, server_default="0"),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_dependency_pred_succ"),
    )
    op.create_index("ix_dependencies_org", "task_dependencies", ["organization_id"])
    op.create_index("ix_dependencies_project", "task_dependencies", ["project_id"])
    op.create_index("ix_dependencies_pred", "task_dependencies", ["predecessor_task_id"])
    op.create_index("ix_dependencies_succ", "task_dependencies", ["successor_task_id"])

    op.create_table(
        "risks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("likelihood", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("impact", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", _enum("risk_status", _RISK_STATUS), nullable=False),
        sa.Column("mitigation", sa.Text(), nullable=True),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_risks_org", "risks", ["organization_id"])
    op.create_index("ix_risks_project", "risks", ["project_id"])

    op.create_table(
        "decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        _project_fk(),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("context", sa.Text(), nullable=False, server_default=""),
        sa.Column("decision", sa.Text(), nullable=False, server_default=""),
        sa.Column("consequences", sa.Text(), nullable=False, server_default=""),
        sa.Column("decided_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_decisions_org", "decisions", ["organization_id"])
    op.create_index("ix_decisions_project", "decisions", ["project_id"])

    # Resolve A17: add the project_members -> projects FK now.
    op.create_foreign_key(
        "fk_project_members_project",
        "project_members",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_project_members_project", "project_members", type_="foreignkey")
    op.drop_table("decisions")
    op.drop_table("risks")
    op.drop_table("task_dependencies")
    op.drop_table("tasks")
    op.drop_table("milestones")
    op.drop_table("project_requirements")
    op.drop_table("project_methodologies")
    op.drop_table("projects")
