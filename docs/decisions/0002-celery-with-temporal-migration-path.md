# ADR-0002: Celery for the MVP worker layer, behind a WorkflowEngine port

- **Status:** Accepted
- **Date:** 2026-06-25

## Context
The platform needs durable background execution of tasks. The requirements name
Celery for the MVP but also require that "a durable workflow system such as
Temporal could replace Celery later without rewriting project-domain logic."

Celery is simple to run (Redis broker, no extra server), well understood, and
sufficient for MVP throughput. Temporal offers stronger durability,
deterministic replay, and built-in retries/timeouts/signals, but adds an
operational component (the Temporal server) and a programming model the MVP does
not yet need.

## Decision
Use Celery + Redis for the MVP. Confine all worker coupling behind a narrow
`WorkflowEngine` port:

```python
class WorkflowEngine(Protocol):
    def submit_execution(self, execution_id: UUID) -> str: ...
    def signal_cancel(self, execution_id: UUID) -> None: ...
    def get_status(self, handle: str) -> EngineStatus: ...
```

Domain services, the state machine, dispatch, evaluation, and remediation depend
only on this port — never on Celery, Redis, or task decorators directly. The
state machine itself lives in the domain layer; workers only *drive events* into
it. Retry/timeout/cancel semantics are expressed as state-machine events, not
Celery-specific features, so they survive an engine swap.

## Consequences
- MVP stays operationally light.
- Replacing Celery with Temporal = implement `TemporalWorkflowEngine` and a thin
  worker entrypoint; no change to project-domain logic.
- Some Temporal-native conveniences (durable timers, signals) are emulated in
  the MVP via DB state + Celery `countdown`/revocation; documented as debt to be
  retired on the Temporal swap.
