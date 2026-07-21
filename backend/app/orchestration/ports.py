"""Provider-neutral ports (interfaces) that protect the core constraints.

Domain code depends ONLY on these Protocols, never on a concrete provider SDK,
Celery, Redis, or a cloud storage client. Concrete adapters live at the edges
(app/orchestration/adapters, app/workers) and are wired in a composition root.

See docs/architecture.md §3 and ADR-0002 / ADR-0003.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


# ── AgentAdapter (model provider seam) ────────────────────────────────────
class ProviderErrorCategory(StrEnum):
    """Bounded, public-safe reasons for a provider call failure."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"


_PROVIDER_DIAGNOSTIC_RE = re.compile(
    "provider_http_status=(none|[1-5][0-9]{2}) "
    "provider_error_category=("
    + "|".join(category.value for category in ProviderErrorCategory)
    + ")"
)


class ProviderCallError(RuntimeError):
    """A provider failure safe to persist, return, and print.

    Raw requests, responses, URLs, headers, prompts, outputs, credentials, and
    underlying exceptions must never be attached to this exception.
    """

    def __init__(
        self,
        *,
        http_status: int | None,
        category: ProviderErrorCategory,
    ) -> None:
        if http_status is not None and not 100 <= http_status <= 599:
            raise ValueError("provider HTTP status must be between 100 and 599")
        self.http_status = http_status
        self.category = category
        status = str(http_status) if http_status is not None else "none"
        self.public_message = (
            f"provider_http_status={status} provider_error_category={category.value}"
        )
        super().__init__(self.public_message)


def parse_provider_diagnostic(message: str | None) -> tuple[int | None, str | None]:
    """Return only an exact allowlisted provider diagnostic.

    Unknown or embellished strings deliberately return null fields instead of
    copying any raw error text into logs or evidence.
    """

    match = _PROVIDER_DIAGNOSTIC_RE.fullmatch(message or "")
    if match is None:
        return None, None
    raw_status, category = match.groups()
    return (None if raw_status == "none" else int(raw_status), category)


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
    """Submit and track durable task execution. Celery now, Temporal later.

    ``work_id`` identifies the schedulable unit — the **Task** id in the MVP
    (execution-attempt rows are created by the worker as it runs). ``params``
    carries the JSON-safe dispatch options (attempts, timeout, evaluation
    config, actor) so the worker runs with the caller's exact intent.
    """

    def submit_execution(self, work_id: UUID, params: dict[str, Any] | None = None) -> str: ...
    def signal_cancel(self, handle: str) -> None: ...
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


# ── EventBus (live domain-event fan-out seam) ─────────────────────────────
@dataclass(frozen=True)
class DomainEvent:
    """A material state change, shaped for streaming consumers.

    Mirrors the audit-event vocabulary (action, entity_type, entity_id,
    actor) so the live stream and the audit trail describe the same reality.
    ``payload`` carries the already-redacted after-image; the stream is
    advisory — the database remains the source of truth.
    """

    organization_id: UUID
    action: str
    entity_type: str
    occurred_at: datetime
    project_id: UUID | None = None
    entity_id: UUID | None = None
    actor_type: str | None = None
    actor_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "organization_id": str(self.organization_id),
            "project_id": str(self.project_id) if self.project_id else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "actor_type": self.actor_type,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload,
        }


@runtime_checkable
class EventBus(Protocol):
    """Publish/subscribe for live domain events. In-memory now, Redis in prod."""

    async def publish(self, event: DomainEvent) -> None: ...

    def subscribe(self, organization_id: UUID) -> EventSubscription: ...


class EventSubscription(Protocol):
    """A live event feed for one organization; async-iterable and closeable."""

    def __aiter__(self) -> EventSubscription: ...
    async def __anext__(self) -> DomainEvent: ...
    async def close(self) -> None: ...
