"""RBAC matrix and the agent-escalation hard rule."""

from __future__ import annotations

import uuid

from app.core.rbac import Action, Actor, authorize
from app.core.roles import ActorType, ProjectRole, SystemRole


def _user(role: SystemRole) -> Actor:
    return Actor(
        actor_type=ActorType.USER,
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        system_role=role,
    )


def test_owner_can_manage_users():
    assert authorize(_user(SystemRole.OWNER), Action.USER_MANAGE)


def test_member_cannot_manage_users():
    assert not authorize(_user(SystemRole.MEMBER), Action.USER_MANAGE)


def test_member_can_view_dashboards():
    assert authorize(_user(SystemRole.MEMBER), Action.DASHBOARD_VIEW)


def test_project_manager_can_create_project_via_project_plane():
    member = _user(SystemRole.MEMBER)
    assert not authorize(member, Action.PROJECT_CREATE)
    assert authorize(member, Action.PROJECT_CREATE, project_role=ProjectRole.MANAGER)


def test_approver_decides_approvals():
    member = _user(SystemRole.MEMBER)
    assert authorize(member, Action.APPROVAL_DECIDE, project_role=ProjectRole.APPROVER)
    assert not authorize(member, Action.APPROVAL_DECIDE, project_role=ProjectRole.CONTRIBUTOR)


def test_agent_cannot_grant_tool_permission():
    agent = Actor(actor_type=ActorType.AGENT, organization_id=uuid.uuid4())
    assert not authorize(agent, Action.TOOL_PERMISSION_GRANT)
    # Even with a (hypothetically) elevated project role, agents are denied.
    assert not authorize(agent, Action.TOOL_PERMISSION_GRANT, project_role=ProjectRole.MANAGER)


def test_agent_cannot_manage_users_or_assign_agents():
    agent = Actor(actor_type=ActorType.AGENT, organization_id=uuid.uuid4())
    assert not authorize(agent, Action.USER_MANAGE)
    assert not authorize(agent, Action.AGENT_ASSIGN)
