"""Agent, capability, tool, permission, and matching schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import (
    AgentKind,
    AgentRole,
    AgentStatus,
    ToolKind,
    ToolSensitivity,
)


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    kind: AgentKind = AgentKind.AI
    provider: str | None = None
    model: str | None = None
    default_role: AgentRole = AgentRole.EITHER
    config: dict | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    kind: AgentKind
    provider: str | None
    model: str | None
    status: AgentStatus
    default_role: AgentRole

    model_config = {"from_attributes": True}


class CapabilityCreate(BaseModel):
    capability: str = Field(min_length=1, max_length=80)
    proficiency: int = Field(default=3, ge=1, le=5)
    evidence: str | None = None


class CapabilityResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    capability: str
    proficiency: int
    evidence: str | None

    model_config = {"from_attributes": True}


class ToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: ToolKind
    description: str = ""
    schema_: dict | None = Field(default=None, alias="schema")
    sensitivity: ToolSensitivity = ToolSensitivity.LOW

    model_config = {"populate_by_name": True}


class ToolResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    kind: ToolKind
    description: str
    sensitivity: ToolSensitivity

    model_config = {"from_attributes": True}


class PermissionGrant(BaseModel):
    scope: dict | None = None
    expires_at: datetime | None = None


class PermissionResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    tool_id: uuid.UUID
    scope: dict | None
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    agent_id: uuid.UUID
    name: str
    eligible: bool
    coverage: float
    matched: list[str]
    missing: list[str]
    score: float


class AssignRequest(BaseModel):
    agent_id: uuid.UUID
