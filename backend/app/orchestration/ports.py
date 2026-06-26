"""Provider-neutral ports (interfaces) that protect the core constraints.

Domain code depends ONLY on these Protocols, never on a concrete provider SDK,
Celery, Redis, or a cloud storage client. Concrete adapters live at the edges
(app/orchestration/adapters, app/workers) and are wired in a composition root.

See docs/architecture.md §3 and ADR-0002 / ADR-0003.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


# ── AgentAdapter (model provider seam) ────────────────────────────────────
@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class AgentRunRequest:
    """A single provider-neutral run request.

    `credential_ref` is the *env-var key* of the credential, never the secret
    value. The adapter resolves it at call time and never returns it.
    """

    prompt: str
    model: str | None = None
    system: str | None = None
    tools: list[ToolSchema] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    credential_ref: str | None = None
    run_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class AgentRunResult:
    output: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_used: int = 0
    cost_estimate: float = 0.0
    provider: str = "unknown"
    raw_id: str | None = None


@runtime_checkable
class AgentAdapter(Protocol):
    """Run a prompt/tool request against some model provider."""

    name: str

    async def run(self, request: AgentRunRequest) -> AgentRunResult: ...


# ── WorkflowEngine (durable worker seam) ──────────────────────────────────
class EngineState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EngineStatus:
    state: EngineState
    detail: str | None = None


@runtime_checkable
class WorkflowEngine(Protocol):
    """Submit and track durable task execution. Celery now, Temporal later."""

    def submit_execution(self, execution_id: UUID) -> str: ...
    def signal_cancel(self, execution_id: UUID) -> None: ...
    def get_status(self, handle: str) -> EngineStatus: ...


# ── ArtifactStore (object storage seam) ───────────────────────────────────
@dataclass(frozen=True)
class StoredArtifact:
    storage_key: str
    size_bytes: int
    sha256: str


@runtime_checkable
class ArtifactStore(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> StoredArtifact: ...
    def get(self, key: str) -> bytes: ...


# ── Clock (testable time source) ──────────────────────────────────────────
@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...
