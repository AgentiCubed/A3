"""Risk and decision schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.enums import RiskStatus


class RiskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    mitigation: str | None = None


class RiskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    likelihood: int
    impact: int
    severity: int
    status: RiskStatus
    mitigation: str | None

    model_config = {"from_attributes": True}


class DecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    context: str = ""
    decision: str = ""
    consequences: str = ""


class DecisionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    context: str
    decision: str
    consequences: str

    model_config = {"from_attributes": True}
