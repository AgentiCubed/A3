# AgentiCubed — System Overview (Visual)

A one-page, diagram-first view of the platform. This complements the prose
[`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) and the detailed
[`architecture.md`](architecture.md); the diagrams below are the same
component and control-loop boundaries drawn visually.

Deeper references: [`data-model`](data-model.md) ·
[`execution-state-machine`](execution-state-machine.md) ·
[`security-model`](security-model.md) · [`roadmap`](roadmap.md) ·
[`demo`](demo.md) · ADRs in [`decisions/`](decisions/).

---

## 1. The control loop

Everything the platform does is one closed loop over each task, run until
acceptance criteria are met.

```mermaid
flowchart LR
    Plan["Plan<br/><small>decompose · methodology</small>"]
    Assign["Assign<br/><small>capability matching</small>"]
    Execute["Execute<br/><small>dispatch · agent adapter</small>"]
    Evaluate["Evaluate<br/><small>rubrics · evaluator agent</small>"]
    Gaps["Identify Gaps<br/><small>gap classifier</small>"]
    Remediate["Remediate<br/><small>policy engine</small>"]

    Plan --> Assign --> Execute --> Evaluate --> Gaps --> Remediate
    Remediate -->|re-execute| Execute
    Evaluate -->|pass + no approval| Done(["COMPLETED"])
    Evaluate -->|pass + approval required| Approval(["AWAITING_APPROVAL"])
    Approval -->|approved| Done
```

| Loop step | Component | Output |
|-----------|-----------|--------|
| Plan | `services/decomposition`, `services/methodology` | Tasks, dependencies, milestones, WBS |
| Assign | `services/matching` | Task → Agent assignments |
| Execute | `orchestration/dispatch` + `workers` + `AgentAdapter` | `TaskExecution` records |
| Evaluate | `evaluation/` | `Evaluation` + `EvaluationCriterion` results |
| Identify Gaps | `evaluation/` (gap classifier) | Structured gap descriptors |
| Remediate | `remediation/policy` | Selected `RemediationAction` + justification |
| Re-execute | back to dispatch | new `TaskExecution`, prior ones immutable |

---

## 2. Layered architecture

Dependencies point **inward**. Domain services never import a model SDK,
Celery/Redis, or FastAPI request objects — only ports.

```mermaid
flowchart TB
    subgraph UI["UI — Next.js / React / TypeScript"]
        direction LR
        dash["dashboards · Kanban · Gantt · dependency graph · approvals"]
    end

    subgraph API["API layer — FastAPI (app/api/v1)"]
        direction LR
        ctl["thin controllers · auth · RBAC · request validation"]
    end

    subgraph SVC["Project-domain services (app/services) — provider-neutral"]
        direction LR
        svc["projects · methodology · decomposition · capability analysis<br/>matching · risk/decision logs · metrics"]
    end

    subgraph ENG["Execution engines"]
        direction LR
        orch["Orchestration<br/>app/orchestration<br/><small>state machine · dispatch</small>"]
        eval["Evaluation<br/>app/evaluation<br/><small>validators + evaluators</small>"]
        rem["Remediation<br/>app/remediation<br/><small>policy engine</small>"]
    end

    subgraph PROV["Provider integrations (app/orchestration/adapters)"]
        direction LR
        prov["MockProvider (deterministic) · Anthropic adapter · extensible"]
    end

    UI -->|"REST/JSON (OpenAPI) · SSE"| API
    API -->|"calls services, never the DB"| SVC
    SVC --> orch
    SVC --> eval
    SVC --> rem
    orch -->|AgentAdapter port| PROV

    XCUT["Cross-cutting: app/core (config · security/RBAC · structured logging · audit) ·<br/>app/db (session + Unit of Work) · app/workers (Celery behind WorkflowEngine port)"]
```

---

## 3. Ports & adapters (the seams that protect the constraints)

Domain code depends only on the ports on the left. Concrete adapters are wired
at the edges, so each can be swapped without touching domain logic.

```mermaid
flowchart LR
    subgraph Domain["Domain (depends only on ports)"]
        d["services · orchestration · evaluation · remediation"]
    end

    subgraph Ports["Ports (Protocol / ABC)"]
        p1["AgentAdapter"]
        p2["WorkflowEngine"]
        p3["ArtifactStore"]
        p4["Clock"]
        p5["EventBus"]
    end

    d --> p1 & p2 & p3 & p4 & p5

    p1 --> a1["MockProvider · AnthropicAdapter"]
    p2 --> a2["CeleryWorkflowEngine<br/><small>→ Temporal later</small>"]
    p3 --> a3["LocalFsArtifactStore<br/><small>→ S3 later</small>"]
    p4 --> a4["SystemClock · FrozenClock (tests)"]
    p5 --> a5["InMemoryEventBus · RedisEventBus<br/><small>feeds the live SSE stream</small>"]
```

| Port | Purpose | MVP adapter(s) | Future swap |
|------|---------|----------------|-------------|
| `AgentAdapter` | Run a prompt/tool-call against a model | `MockProvider`, `AnthropicAdapter` | Any provider |
| `WorkflowEngine` | Enqueue/track durable task execution | `CeleryWorkflowEngine` | `TemporalWorkflowEngine` |
| `ArtifactStore` | Persist project artifacts | `LocalFsArtifactStore` | `S3ArtifactStore` |
| `Clock` | Time source (testable) | `SystemClock` | `FrozenClock` |
| `EventBus` | Live domain-event fan-out (SSE feed) | `InMemoryEventBus`, `RedisEventBus` | NATS / Kafka |

---

## 4. Execution flow (happy path + remediation branch)

```mermaid
sequenceDiagram
    participant Disp as Dispatcher
    participant Eng as WorkflowEngine (Celery)
    participant Wrk as Worker
    participant Ad as AgentAdapter
    participant Ev as Evaluator
    participant Rem as Remediation policy

    Note over Disp: task READY (all deps COMPLETED)
    Disp->>Eng: submit_execution(execution_id)  [READY → QUEUED]
    Eng->>Wrk: deliver job
    Wrk->>Wrk: QUEUED → RUNNING, write immutable TaskExecution
    Wrk->>Ad: run assigned agent
    Ad-->>Wrk: output
    Wrk->>Ev: RUNNING → EVALUATING (separate agent)
    alt pass
        Ev-->>Disp: COMPLETED (or AWAITING_APPROVAL)
    else fail
        Ev->>Rem: gap descriptors
        Rem-->>Disp: RemediationAction → back to QUEUED (prior execution kept)
    end
```

The executor and evaluator of a given `TaskExecution` are always different
agents — enforced by the dispatcher and the API (ADR-0004). Full transition
table: [`execution-state-machine.md`](execution-state-machine.md).

---

## 5. Deployment topology (Docker Compose)

```mermaid
flowchart LR
    browser["Browser"] --> fe["frontend<br/>Next.js :3000"]
    fe --> api["api<br/>FastAPI :8000<br/><small>/docs · /healthz · /readyz</small>"]
    api --> pg[("PostgreSQL 16")]
    api --> redis[("Redis 7")]
    worker["worker<br/>Celery"] --> pg
    worker --> redis
    api -. enqueue .-> redis
    redis -. deliver .-> worker
```

Published ports bind to loopback by default. Bring the stack up with
`docker compose up --build`; run the seeded end-to-end demonstration from the
repo root with `make demo` (see [`demo.md`](demo.md)).

---

## 6. Hard constraints (why the seams exist)

1. **Provider neutrality** — all model interaction goes through `AgentAdapter`;
   no domain module imports a provider SDK.
2. **Durability & auditability** — `TaskExecution`, `Evaluation`, and
   `AuditEvent` are append-only at both the app and DB layers.
3. **Separation of concerns** — project, orchestration, provider, and UI layers
   are independent; dependencies point inward.
4. **Replaceable worker layer** — domain code depends on the `WorkflowEngine`
   port, so Celery can be replaced by Temporal without rewriting domain logic.
