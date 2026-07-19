# AgentiCubed — Architecture

## 1. Goals and constraints

AgentiCubed orchestrates projects executed by a mix of AI agents and humans. The
architecture is built around four hard constraints derived from the project
definition:

1. **Provider neutrality** — orchestration must never depend on a single model
   provider. All model interaction goes through an `AgentAdapter` port.
2. **Durability & auditability** — every execution and evaluation is stored;
   execution history is immutable; material state changes emit audit events.
3. **Separation of concerns** — project logic, orchestration logic, provider
   integrations, and UI are independent layers.
4. **Replaceable worker layer** — Celery powers the MVP, but project-domain
   logic depends only on a `WorkflowEngine` port so Temporal (or similar) can
   replace it without rewriting domain code.

## 2. Layered architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ UI (Next.js / React / TypeScript)                                  │
│   dashboards · Kanban · Gantt · dependency graph · approvals       │
└───────────────▲────────────────────────────────────────────────────┘
                │ REST/JSON (OpenAPI), SSE for live execution updates
┌───────────────┴────────────────────────────────────────────────────┐
│ API layer (FastAPI)  app/api/v1                                      │
│   thin controllers · auth · RBAC enforcement · request validation   │
└───────────────▲────────────────────────────────────────────────────┘
                │ calls services (never the DB directly)
┌───────────────┴────────────────────────────────────────────────────┐
│ Project-domain services  app/services                               │
│   projects · methodology recommender · WBS/decomposition ·          │
│   capability analysis · matching · risk/decision logs · metrics     │
│   ── provider-neutral, no model SDK imports, no Celery imports ──    │
└──────▲───────────────────────────────▲───────────────────▲──────────┘
       │                                │                   │
┌──────┴────────────┐  ┌───────────────┴───────┐  ┌─────────┴──────────┐
│ Orchestration      │  │ Evaluation            │  │ Remediation         │
│ app/orchestration  │  │ app/evaluation        │  │ app/remediation     │
│  state machine ·   │  │  deterministic        │  │  policy engine maps │
│  dispatch ·        │  │  validators +         │  │  evaluation gaps →  │
│  AgentAdapter port │  │  evaluator agents     │  │  remediation action │
└──────▲─────────────┘  └───────────────────────┘  └────────────────────┘
       │ AgentAdapter port (provider-neutral)
┌──────┴──────────────────────────────────────────────────────────────┐
│ Provider integrations  app/orchestration/adapters                    │
│   MockProvider (deterministic) · Anthropic adapter · (extensible)    │
└───────────────────────────────────────────────────────────────────────┘

Cross-cutting: app/core (config, security/RBAC, structured logging, audit),
app/db (SQLAlchemy session + Unit of Work), app/workers (Celery behind the
WorkflowEngine port).
```

### Dependency rule

Dependencies point **inward**. The domain-services layer must not import:
- any model-provider SDK,
- Celery / Redis client code,
- FastAPI request objects.

It depends only on **ports** (Python `Protocol`/ABC interfaces): `AgentAdapter`,
`WorkflowEngine`, `ArtifactStore`, `Clock`. Concrete adapters are wired at the
edges via dependency injection (FastAPI `Depends` + a small composition root in
`app/core/container.py`).

## 3. Ports and adapters (the seams that protect the constraints)

| Port | Purpose | MVP adapter(s) | Future swap |
|------|---------|----------------|-------------|
| `AgentAdapter` | Run a prompt/tool-call against a model | `MockProvider`, `AnthropicProvider`, `GitHubModelsProvider` | Any provider |
| `WorkflowEngine` | Enqueue/track durable task execution | `CeleryWorkflowEngine` | `TemporalWorkflowEngine` |
| `ArtifactStore` | Persist project artifacts (binary/text) | `LocalFsArtifactStore` | `S3ArtifactStore` |
| `Clock` | Time source (testable) | `SystemClock` | `FrozenClock` (tests) |
| `EventBus` | Live domain-event fan-out (SSE feed) | `InMemoryEventBus`, `RedisEventBus` | NATS / Kafka |

The `WorkflowEngine` port is deliberately narrow:

```python
class WorkflowEngine(Protocol):
    def submit_execution(self, execution_id: UUID) -> str: ...   # returns engine handle
    def signal_cancel(self, execution_id: UUID) -> None: ...
    def get_status(self, handle: str) -> EngineStatus: ...
```

Because domain code only knows this port, swapping Celery → Temporal means
implementing the port again; the state machine, dispatch, and project logic do
not change. See `docs/decisions/0002-celery-with-temporal-migration-path.md`.

## 4. The control loop, mapped to components

| Loop step | Component | Output |
|-----------|-----------|--------|
| Plan | `services/decomposition`, `services/methodology` | Tasks, dependencies, milestones, WBS |
| Assign | `services/matching` | Task → Agent assignments |
| Execute | `orchestration/dispatch` + `workers` + `AgentAdapter` | `TaskExecution` records |
| Evaluate | `evaluation/` | `Evaluation` + `EvaluationCriterion` results |
| Identify Gaps | `evaluation/` (gap classifier) | Structured gap descriptors |
| Remediate | `remediation/policy` | Selected `RemediationAction` + justification |
| Re-execute | back to dispatch | new `TaskExecution`, prior ones immutable |

## 5. Execution flow (happy path)

1. Task enters `READY` once all dependencies are `COMPLETED` (dependency check
   rejects cycles — see §7).
2. Dispatcher moves `READY → QUEUED` and calls `WorkflowEngine.submit_execution`.
3. Worker pulls the job, transitions `QUEUED → RUNNING`, creates an immutable
   `TaskExecution` row, invokes the assigned agent through `AgentAdapter`.
4. On completion → `RUNNING → EVALUATING`. Evaluator (separate from executor)
   scores output against rubric criteria.
5. Pass + no approval required → `COMPLETED`. Pass + approval required →
   `AWAITING_APPROVAL`. Fail → remediation policy decides next action; task may
   go `FAILED`, `BLOCKED`, or loop back to `QUEUED` with a remediation applied.

Full diagram and transition table: `docs/execution-state-machine.md`.

## 6. Executor / evaluator separation

A single agent is never both the executor and the evaluator of the same
`TaskExecution`. The dispatcher enforces this: the evaluator agent (or
deterministic validator) is resolved from a different registry slot, and the API
rejects evaluator assignments that collide with the executor. This is a
correctness and anti-gaming control, recorded as ADR-0004.

## 7. Dependency-graph integrity

`TaskDependency` edges form a DAG per project. On every dependency create/update
the service runs a cycle check (DFS / Kahn's algorithm). A would-be cycle is
rejected with `409 Conflict` and an audit event. Critical-path and Gantt
computations assume an acyclic graph and rely on this invariant.

## 8. Transactions and immutability

- Important state transitions (task status change + audit event + execution row)
  run inside a single DB transaction via a Unit-of-Work helper.
- `TaskExecution`, `Evaluation`, and `AuditEvent` are **append-only**. Updates
  are modeled as new rows; the ORM blocks `UPDATE`/`DELETE` on these tables at
  the application layer, and DB triggers reinforce it (Phase 2).

## 9. Observability

- **Structured logging** (JSON) via `structlog`, with request id, project id,
  task id, execution id, and actor id bound to the log context.
- **Health checks**: `/healthz` (liveness), `/readyz` (DB + Redis reachability).
- **Metrics**: project/agent metrics persisted as `ProjectMetric` /
  `AgentMetric`; Prometheus `/metrics` exposes request counts and latency
  histograms labeled by route template.
- **Live events**: every audited state change is published through the
  `EventBus` port and streamed per project over SSE
  (`GET /api/v1/projects/{id}/events`). The stream is advisory (at-most-once,
  pre-commit); the database remains the source of truth.

## 10. Security posture (summary)

RBAC at org + project scope, least-privilege tool permissions per agent, secrets
never in prompts/logs/code/ordinary data fields, human approval gates before
irreversible actions, agents barred from changing their own permissions. Full
detail in `docs/security-model.md`.

## 11. Technology substitutions

Any deviation from the default stack is recorded as an ADR in
`docs/decisions/`. Current ADRs:

- ADR-0001 — Record architecture decisions
- ADR-0002 — Celery for MVP with a Temporal migration path
- ADR-0003 — Provider-neutral AgentAdapter as the only model seam
- ADR-0004 — Mandatory executor/evaluator separation
