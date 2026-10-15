"""Project, methodology, requirement, milestone schemas."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import (
    Methodology,
    MilestoneStatus,
    ProjectStatus,
    RecommendedBy,
    RequirementKind,
    RequirementPriority,
)

AcceptanceCheck = Literal[
    "non_empty",
    "min_length",
    "max_length",
    "contains_all",
    "contains_any",
    "is_json",
    "regex",
]

_DELIVERABLE_SEPARATORS_RE = re.compile(r"[\s_\-]+")


def normalize_deliverable_name(name: str) -> str:
    """Return the canonical form used for deliverable-name matching."""
    return _DELIVERABLE_SEPARATORS_RE.sub("", name.lower())


class SignalsIn(BaseModel):
    requirements_stable: bool = False
    hard_deadline: bool = False
    many_dependencies: bool = False
    continuous_flow: bool = False
    resource_constrained: bool = False


class AcceptanceCriterionIn(BaseModel):
    """One deterministic project-acceptance rubric criterion.

    This is the canonical validation boundary for both API input and persisted
    JSON. Keeping the per-check parameter contract here prevents malformed
    specifications from reaching the rubric evaluator and raising at close time.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str | None = Field(default=None, min_length=1, max_length=80)
    check: AcceptanceCheck
    params: dict[str, object] = Field(default_factory=dict)
    weight: float = Field(default=1.0, gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_check_params(self) -> AcceptanceCriterionIn:
        params = self.params

        if self.check in {"non_empty", "is_json"}:
            if params:
                raise ValueError(f"{self.check} does not accept parameters")
            return self

        if self.check in {"min_length", "max_length"}:
            param_name = "min" if self.check == "min_length" else "max"
            unknown = set(params) - {param_name}
            if unknown:
                raise ValueError(
                    f"{self.check} has unsupported parameters: {', '.join(sorted(unknown))}"
                )
            if param_name in params:
                value = params[param_name]
                minimum = 1 if self.check == "min_length" else 0
                if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                    raise ValueError(
                        f"{self.check} parameter '{param_name}' must be an integer >= {minimum}"
                    )
            return self

        if self.check in {"contains_all", "contains_any"}:
            if set(params) != {"keywords"}:
                raise ValueError(f"{self.check} requires only the 'keywords' parameter")
            keywords = params["keywords"]
            if not isinstance(keywords, list) or not keywords:
                raise ValueError(f"{self.check} keywords must be a non-empty list of strings")
            cleaned: list[str] = []
            for keyword in keywords:
                if not isinstance(keyword, str) or not keyword.strip():
                    raise ValueError(f"{self.check} keywords must be a non-empty list of strings")
                cleaned.append(keyword.strip())
            self.params = {"keywords": cleaned}
            return self

        if self.check == "regex":
            if set(params) != {"pattern"}:
                raise ValueError("regex requires only the 'pattern' parameter")
            pattern = params["pattern"]
            if not isinstance(pattern, str) or not pattern.strip():
                raise ValueError("regex pattern must be a non-empty string")
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"regex pattern is invalid: {exc}") from exc
            self.params = {"pattern": pattern}
            return self

        raise ValueError(f"unsupported acceptance check: {self.check}")


class AcceptanceCriteriaIn(BaseModel):
    """Canonical project-acceptance specification for API and stored JSON."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    criteria: list[AcceptanceCriterionIn] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)

    @field_validator("deliverables")
    @classmethod
    def validate_deliverables(cls, deliverables: list[str]) -> list[str]:
        cleaned: list[str] = []
        for deliverable in deliverables:
            name = deliverable.strip()
            normalized = normalize_deliverable_name(name)
            if not name or not normalized or not any(char.isalnum() for char in normalized):
                raise ValueError("deliverables must contain non-empty names, not only separators")
            cleaned.append(name)
        return cleaned


def validate_acceptance_criteria(spec: object) -> AcceptanceCriteriaIn:
    """Validate API or persisted acceptance JSON through one strict contract."""
    return AcceptanceCriteriaIn.model_validate(spec)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    objective: str = ""
    acceptance_criteria: AcceptanceCriteriaIn | None = None
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
    # Operator halt switch: non-null means the scheduler dispatches nothing new.
    halted_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectHaltRequest(BaseModel):
    """Optional operator context recorded in the project.halted audit event."""

    reason: str | None = Field(default=None, max_length=500)


class ProjectHaltResponse(BaseModel):
    project_id: uuid.UUID
    status: ProjectStatus
    halted_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectCloseRequest(BaseModel):
    """Close options (WS-4b). Closing with unmet acceptance criteria requires
    explicit acknowledgment — deliberate abandonment, recorded in the audit."""

    acknowledge_unmet_criteria: bool = False


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
