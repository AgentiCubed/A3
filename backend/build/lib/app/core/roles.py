"""Role and actor vocabularies shared by RBAC, models, and services.

Kept dependency-free (no SQLAlchemy/FastAPI imports) so both the domain and the
infrastructure layers can import it without cycles.
"""

from __future__ import annotations

from enum import StrEnum


class SystemRole(StrEnum):
    """Organization-plane role, stored on the User row."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ProjectRole(StrEnum):
    """Project-plane role, resolved per request from ProjectMember."""

    MANAGER = "manager"
    CONTRIBUTOR = "contributor"
    APPROVER = "approver"
    VIEWER = "viewer"


class ActorType(StrEnum):
    """Who is performing an action. Agents are first-class but constrained."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
