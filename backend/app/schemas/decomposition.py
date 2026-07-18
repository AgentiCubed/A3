"""Versioned objective-to-plan schemas (WS-6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DecompositionPlanStatus, DependencyType
from app.schemas.project import AcceptanceCriteriaIn, AcceptanceCriterionIn


class PlanTaskIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    estimate_hours: float = Field(default=0.0, ge=0, le=10_000)
    required_capabilities: list[str] = Field(default_factory=list, max_length=20)
    priority: int = Field(default=3, ge=1, le=5)
    acceptance_criteria: list[AcceptanceCriterionIn] = Field(min_length=1, max_length=20)


class PlanDependencyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predecessor_key: str = Field(min_length=1, max_length=80)
    successor_key: str = Field(min_length=1, max_length=80)
    dependency_type: DependencyType = DependencyType.FINISH_TO_START
    lag_hours: float = Field(default=0.0, ge=0, le=10_000)


class PlanSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[PlanTaskIn] = Field(min_length=1, max_length=50)
    dependencies: list[PlanDependencyIn] = Field(default_factory=list, max_length=200)
    project_acceptance: AcceptanceCriteriaIn
    assumptions: list[str] = Field(default_factory=list, max_length=50)
    warnings: list[str] = Field(default_factory=list, max_length=50)


class PlanGenerateRequest(BaseModel):
    planner_agent_id: uuid.UUID


class PlanRejectRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class DecompositionPlanResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    planner_agent_id: uuid.UUID | None
    contract_version: str
    version: int
    objective: str
    objective_sha256: str
    status: DecompositionPlanStatus
    plan_spec: PlanSpec | None
    plan_spec_sha256: str | None
    provider_output_sha256: str | None
    provider_output_chars: int
    error_code: str | None
    diagnostic: str | None
    decided_by: uuid.UUID | None
    decided_at: datetime | None
    decision_comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
