"""Project, methodology, requirement, milestone schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import (
    Methodology,
    MilestoneStatus,
    ProjectStatus,
    RecommendedBy,
    RequirementKind,
    RequirementPriority,
)


class SignalsIn(BaseModel):
    requirements_stable: bool = False
    hard_deadline: bool = False
    many_dependencies: bool = False
    continuous_flow: bool = False
    resource_constrained: bool = False


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    objective: str = ""
    acceptance_criteria: dict | None = None
    signals: SignalsIn | None = None


class MethodologyResponse(BaseModel):
    methodology: Methodology
    recommended_by: RecommendedBy
    rationale: str
    config: dict | None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    objective: str
    status: ProjectStatus
    acceptance_criteria: dict | None

    model_config = {"from_attributes": True}


class ProjectWithMethodology(ProjectResponse):
    methodology: MethodologyResponse | None = None


class RequirementCreate(BaseModel):
    kind: RequirementKind
    text: str = Field(min_length=1)
    priority: RequirementPriority = RequirementPriority.SHOULD
    source: str | None = None


class RequirementResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    kind: RequirementKind
    text: str
    priority: RequirementPriority
    source: str | None

    model_config = {"from_attributes": True}


class MilestoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: datetime | None = None
    order_index: int = 0


class MilestoneResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    due_date: datetime | None
    status: MilestoneStatus
    order_index: int

    model_config = {"from_attributes": True}
