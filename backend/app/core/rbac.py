"""Role-based access control.

Two role planes (system + project) checked by a single ``authorize`` function.
This module is pure (no FastAPI/DB imports); the API layer wraps it in a
dependency (see app/api/deps.py) and services re-scope by organization.

Hard rules independent of the matrix:
- ``actor_type == AGENT`` is denied every management action here. Agents execute
  tasks; they never create projects, assign agents, grant tool permissions, or
  manage users. This is one of the three layers preventing self-escalation
  (security-model §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.core.roles import ActorType, ProjectRole, SystemRole


class Action(StrEnum):
    PROJECT_CREATE = "project.create"
    PROJECT_EDIT = "project.edit"
    TASK_EDIT = "task.edit"
    AGENT_ASSIGN = "agent.assign"
    TOOL_PERMISSION_GRANT = "tool_permission.grant"
    APPROVAL_DECIDE = "approval.decide"
    DASHBOARD_VIEW = "dashboard.view"
    USER_MANAGE = "user.manage"


@dataclass(frozen=True)
class Actor:
    actor_type: ActorType
    organization_id: UUID
    user_id: UUID | None = None
    system_role: SystemRole | None = None


# (allowed system roles, allowed project roles) per action. An actor is permitted
# if their system role is allowed OR a supplied project role is allowed.
_MATRIX: dict[Action, tuple[set[SystemRole], set[ProjectRole]]] = {
    Action.PROJECT_CREATE: ({SystemRole.OWNER, SystemRole.ADMIN}, {ProjectRole.MANAGER}),
    Action.PROJECT_EDIT: (
        {SystemRole.OWNER, SystemRole.ADMIN},
        {ProjectRole.MANAGER, ProjectRole.CONTRIBUTOR},
    ),
    Action.TASK_EDIT: (
        {SystemRole.OWNER, SystemRole.ADMIN},
        {ProjectRole.MANAGER, ProjectRole.CONTRIBUTOR},
    ),
    Action.AGENT_ASSIGN: ({SystemRole.OWNER, SystemRole.ADMIN}, {ProjectRole.MANAGER}),
    Action.TOOL_PERMISSION_GRANT: (
        {SystemRole.OWNER, SystemRole.ADMIN},
        {ProjectRole.MANAGER},
    ),
    Action.APPROVAL_DECIDE: ({SystemRole.OWNER, SystemRole.ADMIN}, {ProjectRole.APPROVER}),
    Action.DASHBOARD_VIEW: (
        {SystemRole.OWNER, SystemRole.ADMIN, SystemRole.MEMBER},
        {
            ProjectRole.MANAGER,
            ProjectRole.CONTRIBUTOR,
            ProjectRole.APPROVER,
            ProjectRole.VIEWER,
        },
    ),
    Action.USER_MANAGE: ({SystemRole.OWNER, SystemRole.ADMIN}, set()),
}

# Mutating management actions an agent must never perform.
_AGENT_FORBIDDEN: frozenset[Action] = frozenset(_MATRIX.keys())


def authorize(actor: Actor, action: Action, *, project_role: ProjectRole | None = None) -> bool:
    """Return True if ``actor`` may perform ``action`` (optionally within a project)."""
    if actor.actor_type == ActorType.AGENT and action in _AGENT_FORBIDDEN:
        return False
    if actor.actor_type == ActorType.SYSTEM:
        # The internal system actor is trusted for orchestration bookkeeping only;
        # it is never the path for user-facing management mutations.
        return action in {Action.DASHBOARD_VIEW}

    allowed_system, allowed_project = _MATRIX[action]
    if actor.system_role is not None and actor.system_role in allowed_system:
        return True
    if project_role is not None and project_role in allowed_project:
        return True
    return False
