"""agents, capabilities, tools, permissions, prompt templates

Revision ID: 0004_agents_tools
Revises: 0003_projects_planning
Create Date: 2026-06-25

Phase 4. Agent registry + capabilities, tool registry, default-deny agent-tool
permissions, prompt templates. Also adds the deferred tasks.assigned_agent_id FK.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0004_agents_tools"
down_revision: Union[str, None] = "0003_projects_planning"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_AGENT_KIND = ("ai", "human")
_AGENT_STATUS = ("active", "disabled")
_AGENT_ROLE = ("executor", "evaluator", "either")
_TOOL_KIND = ("http", "python_fn", "shell", "data_source")
_TOOL_SENSITIVITY = ("low", "medium", "high")
_PROMPT_ROLE = ("executor", "evaluator")


def _enum(name: str, values: tuple[str, ...]) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def _org_fk() -> sa.Column:
    return sa.Column(
        "organization_id",
        sa.Uuid(),
        sa.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )


def _ts(col: str) -> sa.Column:
    return sa.Column(col, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("role", _enum("prompt_role", _PROMPT_ROLE), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_prompt_templates_org", "prompt_templates", ["organization_id"])

    op.create_table(
        "agents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", _enum("agent_kind", _AGENT_KIND), nullable=False),
        sa.Column("provider", sa.String(60), nullable=True),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column(
            "prompt_template_id",
            sa.Uuid(),
            sa.ForeignKey("prompt_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", _enum("agent_status", _AGENT_STATUS), nullable=False),
        sa.Column("default_role", _enum("agent_role", _AGENT_ROLE), nullable=False),
        sa.Column("config", sa.JSON(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_agents_org", "agents", ["organization_id"])

    op.create_table(
        "agent_capabilities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability", sa.String(80), nullable=False),
        sa.Column("proficiency", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("evidence", sa.Text(), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("agent_id", "capability", name="uq_agent_capability"),
    )
    op.create_index("ix_agent_caps_org", "agent_capabilities", ["organization_id"])
    op.create_index("ix_agent_caps_agent", "agent_capabilities", ["agent_id"])

    op.create_table(
        "tools",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", _enum("tool_kind", _TOOL_KIND), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("schema", sa.JSON(), nullable=True),
        sa.Column("sensitivity", _enum("tool_sensitivity", _TOOL_SENSITIVITY), nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
    )
    op.create_index("ix_tools_org", "tools", ["organization_id"])

    op.create_table(
        "agent_tool_permissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("agent_id", sa.Uuid(), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tool_id", sa.Uuid(), sa.ForeignKey("tools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=True),
        sa.Column("granted_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool_permission"),
    )
    op.create_index("ix_atp_org", "agent_tool_permissions", ["organization_id"])
    op.create_index("ix_atp_agent", "agent_tool_permissions", ["agent_id"])
    op.create_index("ix_atp_tool", "agent_tool_permissions", ["tool_id"])

    # Resolve the deferred tasks.assigned_agent_id FK now that agents exist.
    op.create_foreign_key(
        "fk_tasks_assigned_agent",
        "tasks",
        "agents",
        ["assigned_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_tasks_assigned_agent", "tasks", type_="foreignkey")
    op.drop_table("agent_tool_permissions")
    op.drop_table("tools")
    op.drop_table("agent_capabilities")
    op.drop_table("agents")
    op.drop_table("prompt_templates")
