"""Execution dispatch and history schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.orchestration.state_machine.states import ExecutionState


class DispatchRequest(BaseModel):
    max_attempts: int = Field(default=2, ge=1, le=10)
    timeout_s: float = Field(default=30.0, gt=0, le=600)


class DispatchResultResponse(BaseModel):
    final_state: ExecutionState
    attempts: int
    escalated: bool
    output: str | None
    execution_ids: list[uuid.UUID]


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: uuid.UUID | None
    attempt_number: int
    state: ExecutionState
    output: str | None
    error: str | None
    provider: str | None
    tokens_used: int
    cost_estimate: float
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class ReassignRequest(BaseModel):
    agent_id: uuid.UUID
