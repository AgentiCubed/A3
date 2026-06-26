"""ORM model registry.

Importing this package registers every model on ``Base.metadata`` (so Alembic
autogenerate and test ``create_all`` see them). Add new models to ``__all__`` and
the imports below as later phases land.
"""

from __future__ import annotations

from app.models.audit_event import AuditEvent
from app.models.organization import Organization
from app.models.user import ProjectMember, User

__all__ = ["AuditEvent", "Organization", "ProjectMember", "User"]
