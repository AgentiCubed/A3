"""Approval schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.enums import ApprovalStatus, RiskLevel


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    task_execution_id: uuid.UUID | None
    requested_action: str
    risk_level: RiskLevel
    status: ApprovalStatus
    decided_by: uuid.UUID | None
    decided_at: datetime | None
    comment: str | None

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    approve: bool
    comment: str | None = None
