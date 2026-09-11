"""Organization management schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.roles import SystemRole


class RoleUpdateRequest(BaseModel):
    system_role: SystemRole
