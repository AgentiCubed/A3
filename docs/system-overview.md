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
flowchart TD
    %% Styling classes for visual hierarchy
    classDef normalTask fill:#e6f3ff,stroke:#1f77b4,stroke-width:2px,color:#000
    classDef warningTask fill:#fff2e6,stroke:#ff7f0e,stroke-width:2px,color:#000
    classDef successState fill:#e6ffe6,stroke:#2ca02c,stroke-width:2px,color:#000
    classDef pendingState fill:#f2e6ff,stroke:#9467bd,stroke-width:2px,color:#000

    Plan["Plan \n(Decompose & Methodology)"]:::normalTask
    Assign["Assign \n(Capability Matching)"]:::normalTask
    Execute["Execute \n(Dispatch & Agent Adapter)"]:::normalTask
    Evaluate["Evaluate \n(Rubrics & Evaluator Agent)"]:::normalTask
    
    Gaps["Identify Gaps \n(Gap Classifier)"]:::warningTask
    Remediate["Remediate \n(Policy Engine)"]:::warningTask
    
    Done(["COMPLETED"]):::successState
    Approval(["AWAITING_APPROVAL"]):::pendingState

    %% Main execution flow
    Plan --> Assign
    Assign --> Execute
    Execute --> Evaluate
    
    %% Branching logic based on evaluation
    Evaluate -->|Fail: Gaps found| Gaps
    Evaluate -->|Pass: No approval needed| Done
    Evaluate -->|Pass: Approval required| Approval
    
    Approval -->|Approved| Done
    
    %% The closed remediation loop
    Gaps --> Remediate
    Remediate -->|Re-execute| Execute
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
    %% Styling classes
    classDef component fill:#e6f3ff,stroke:#1f77b4,stroke-width:2px,color:#000,rx:5,ry:5
    classDef crosscut fill:#fff2e6,stroke:#ff7f0e,stroke-width:2px,color:#000,rx:5,ry:5

    subgraph UI ["1. UI (Next.js / React / TypeScript)"]
        direction TB
        dash["Dashboards, Kanban, Gantt, \nDependency Graph, Approvals"]:::component
    end

    subgraph API ["2. API Layer (FastAPI app/api/v1)"]
        direction TB
        ctl["Thin Controllers, Auth, \nRBAC, Request Validation"]:::component
    end

    subgraph SVC ["3. Project-Domain Services (app/services)"]
        direction TB
        svc["Projects, Methodology, Decomposition, \nCapability Analysis, Matching, \nRisk/Decision Logs, Metrics"]:::component
    end

    subgraph ENG ["4. Execution Engines"]
        direction LR
        orch["Orchestration (app/orchestration)\n State Machine, Dispatch"]:::component
        eval["Evaluation (app/evaluation)\n Validators, Evaluators"]:::component
        rem["Remediation (app/remediation)\n Policy Engine"]:::component
    end

    subgraph PROV ["5. Provider Integrations (app/orchestration/adapters)"]
        direction TB
        prov["MockProvider (Deterministic), \nOpenAICompatible (gemini, ollama), \nAnthropic Adapter"]:::component
    end

    XCUT["Cross-cutting: app/core (Config, Security/RBAC, Logging, Audit) \n app/db (Session, Unit of Work) \n app/workers (Celery behind WorkflowEngine port)"]:::crosscut

    %% Dependencies point INWARD
    UI -->|"REST/JSON (OpenAPI), SSE"| API
    API -->|"Calls services, never the DB"| SVC
    SVC --> orch
    SVC --> eval
    SVC --> rem
    orch -->|"AgentAdapter port"| PROV
```

---

## 3. Ports & adapters (the seams that protect the constraints)

Domain code depends only on the ports on the left. Concrete adapters are wired
at the edges, so each can be swapped without touching domain logic.

```mermaid
flowchart LR
    %% Styling classes for visual distinction and accessibility
    classDef domain fill:#f2e6ff,stroke:#9467bd,stroke-width:2px,color:#000,rx:5,ry:5
    classDef port fill:#fff2e6,stroke:#ff7f0e,stroke-width:2px,color:#000,shape:hexagon
    classDef adapter fill:#e6ffe6,stroke:#2ca02c,stroke-width:2px,color:#000,rx:5,ry:5

    subgraph DomainLayer ["1. Domain (Depends only on ports)"]
        direction TB
        D["Domain Logic: \nServices, Orchestration, \nEvaluation, Remediation"]:::domain
    end

    subgraph PortLayer ["2. Ports (Protocol / ABC)"]
        direction TB
        P1{{"AgentAdapter"}}:::port
        P2{{"WorkflowEngine"}}:::port
        P3{{"ArtifactStore"}}:::port
        P4{{"Clock"}}:::port
        P5{{"EventBus"}}:::port
    end

    subgraph AdapterLayer ["3. Concrete Adapters (Interchangeable)"]
        direction TB
        A1["MockProvider, OpenAICompatibleProvider \n(gemini, ollama), AnthropicProvider"]:::adapter
        A2["Celery (Future: Temporal)"]:::adapter
        A3["LocalFs (Future: S3)"]:::adapter
        A4["SystemClock, FrozenClock"]:::adapter
        A5["InMemory, Redis (SSE feed)"]:::adapter
    end

    %% Dependency flow
    D -->|Calls interface| P1
    D --> P2
    D --> P3
    D --> P4
    D --> P5

    %% Implementation flow (Dotted lines show dependency inversion)
    P1 -.->|Realized by| A1
    P2 -.-> A2
    P3 -.-> A3
    P4 -.-> A4
    P5 -.-> A5
```

| Port | Purpose | MVP adapter(s) | Future swap |
|------|---------|----------------|-------------|
| `AgentAdapter` | Run a prompt/tool-call against a model | `MockProvider`, `OpenAICompatibleProvider` (registry entries `gemini`, `ollama`), `AnthropicProvider`; `github_models` remains as a retirement tombstone | Any OpenAI-compatible endpoint is a registry entry, not new code |
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
flowchart TD
    %% Styling classes
    classDef client fill:#e6f3ff,stroke:#1f77b4,stroke-width:2px,color:#000
    classDef server fill:#f2e6ff,stroke:#9467bd,stroke-width:2px,color:#000
    classDef database fill:#fff2e6,stroke:#ff7f0e,stroke-width:2px,color:#000
    classDef worker fill:#e6ffe6,stroke:#2ca02c,stroke-width:2px,color:#000

    browser["Browser"]:::client
    fe["Frontend \n Next.js :3000"]:::client
    api["API \n FastAPI :8000 \n /docs · /healthz · /readyz"]:::server
    
    pg[("PostgreSQL 16")]:::database
    redis[("Redis 7")]:::database
    
    worker["Worker \n Celery"]:::worker

    %% Standard connections
    browser --> fe
    fe --> api
    api --> pg
    api --> redis
    worker --> pg
    worker --> redis
    
    %% Queue flow
    api -.->|"enqueue"| redis
    redis -.->|"deliver"| worker
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
