"""Execution dispatch and history schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import Verdict
from app.orchestration.state_machine.states import ExecutionState


class DispatchRequest(BaseModel):
    max_attempts: int = Field(default=2, ge=1, le=10)
    timeout_s: float = Field(default=30.0, gt=0, le=600)
    # Optional closed-loop evaluation. Omit for a plain run that completes on success.
    rubric: list[dict] | None = None
    evaluator_agent_id: uuid.UUID | None = None
    max_remediations: int = Field(default=1, ge=0, le=5)


class DispatchAcceptedResponse(BaseModel):
    """Async dispatch (WORKFLOW_ENGINE_BACKEND=celery): queued, not yet run.

    The final outcome is not known at response time — poll the executions
    endpoint or subscribe to the project's SSE event stream.
    """

    task_id: uuid.UUID
    status: ExecutionState  # QUEUED
    engine: str
    engine_handle: str


class ProjectStartRequest(BaseModel):
    """Options applied to every task the scheduling pass dispatches."""

    max_attempts: int = Field(default=2, ge=1, le=10)
    timeout_s: float = Field(default=30.0, gt=0, le=600)


class StartedTaskResponse(BaseModel):
    task_id: uuid.UUID
    status: ExecutionState


class ProjectStartResponse(BaseModel):
    """Outcome of a project-level scheduling pass.

    In celery mode ``tasks`` are the initial QUEUED wave; the worker dispatches
    successors as their predecessors complete. In inline mode the whole
    dependency chain has already run and ``tasks`` hold final states.
    """

    engine: str
    tasks: list[StartedTaskResponse]


class DispatchResultResponse(BaseModel):
    final_state: ExecutionState
    attempts: int
    escalated: bool
    output: str | None
    execution_ids: list[uuid.UUID]
    verdict: Verdict | None = None
    remediations: int = 0


class EvaluationResponse(BaseModel):
    id: uuid.UUID
    task_execution_id: uuid.UUID
    evaluator_agent_id: uuid.UUID | None
    evaluator_kind: str
    verdict: Verdict
    score: float
    summary: str
    gaps: list | None

    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    agent_id: uuid.UUID | None
    attempt_number: int
    state: ExecutionState
    # What was fed in: prompt size plus any predecessor-output handoff (WS-3).
    input_context: dict | None
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
