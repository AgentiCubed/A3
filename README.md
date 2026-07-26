# AgentiCubed

**Agentic project-orchestration platform** that manages projects performed by AI agents and human contributors.

AgentiCubed converts project objectives into structured plans, recommends a project-management methodology, decomposes work into tasks, identifies required capabilities, assigns specialized agents, executes tasks, evaluates outputs, detects failures, remediates the agent/tool configuration, and continues until acceptance criteria are satisfied.

## Principal control loop

```
Plan → Assign → Execute → Evaluate → Identify Gaps → Remediate → Re-execute
```

## Modules

1. Project intake and requirements
2. Methodology recommendation
3. Work decomposition
4. Capability analysis
5. Agent registry
6. Task-to-agent matching
7. Orchestration and execution
8. Output evaluation
9. Closed-loop remediation
10. Human approval
11. Governance and auditing
12. Analytics and reporting
13. Project closeout and retrospective

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, React |
| Backend | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Data | PostgreSQL 16, Redis 7 |
| Workers | Celery (MVP), abstracted behind a `WorkflowEngine` port so Temporal can replace it later |
| Infra | Docker, Docker Compose |
| Visualization | Recharts / Plotly, Mermaid for dependency graphs |
| Analysis | Python + R analysis workers |
| Testing | Pytest, Vitest + React Testing Library, Playwright (E2E) |

## Repository layout

```
agenticubed/
├── docs/                  # Architecture, data model, security, state machine, ADRs
├── backend/               # FastAPI app, orchestration, workers, migrations, tests
│   └── app/
│       ├── api/           # HTTP routes (versioned)
│       ├── core/          # Config, security, logging, RBAC
│       ├── db/            # Session, base, unit-of-work
│       ├── models/        # SQLAlchemy ORM entities
│       ├── schemas/       # Pydantic request/response/domain models
│       ├── services/      # Project-domain logic (provider-neutral)
│       ├── orchestration/ # State machine + provider-neutral agent adapters
│       ├── evaluation/    # Deterministic validators + evaluator agents
│       ├── remediation/   # Closed-loop remediation policy engine
│       └── workers/       # Celery tasks behind the WorkflowEngine port
├── frontend/              # Next.js app
├── analysis/              # Python + R analysis workers
├── infra/                 # Dockerfiles, compose, init scripts
├── seed/                  # Seed data + demonstration project
└── scripts/               # Dev/ops helper scripts
```

## Quick start

> Requires Docker + Docker Compose. Copy the environment template first.

```bash
cp .env.example .env
docker compose up --build          # starts db, redis, api, worker, frontend
# API docs:        http://localhost:8000/docs
# Health:          http://localhost:8000/healthz
# Metrics:         http://localhost:8000/metrics  (Prometheus)
# Frontend:        http://localhost:3000
```

Backend-only local dev (no Docker):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

## Demo

The end-to-end demonstration runs **host-side** (not inside a container). Postgres and Redis
may run through Docker Compose, and the backend Python analysis dependencies are required.
`Rscript` is optional and adds a cross-check; it is not required for the governed proof.

> **Note:** `docker compose exec api python -m app.seed.demo` is **not** a supported v1.0.x
> path. The container image intentionally does not include pandas, matplotlib, or R for v1.0.x.

```bash
# 1. Start infrastructure
docker compose up -d db redis

# 2. Create and activate a host virtualenv
cd backend
python -m venv .venv
source .venv/bin/activate

# 3. Install backend dependencies (including dev and analysis extras)
pip install -e ".[dev,analysis]"

# 4. Apply migrations (loopback URLs — the compose db is exposed on localhost:5432)
DATABASE_URL_SYNC="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" \
  .venv/bin/alembic upgrade head

# 5. Run the demo (artifacts are written outside the repository)
DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" \
DATABASE_URL_SYNC="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" \
REDIS_URL="redis://localhost:6379/0" \
CELERY_BROKER_URL="redis://localhost:6379/1" \
ARTIFACT_STORE_PATH="/tmp/agenticubed-demo-artifacts" \
  .venv/bin/python -m app.seed.demo
```

`POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` default to `agenticubed` in the
`.env.example` template.

`make demo` is a convenience shorthand only when the required environment is already
configured (virtualenv active, env vars exported). A bare `make demo` on a fresh checkout
is **not** sufficient — follow the steps above first.

The reproducible demo does **not** call a live language model. `MockProvider` produces the
plan and agent responses deterministically, while the permissioned pandas analysis,
matplotlib chart generation, and content-addressed artifact storage are real. To include the
optional R statistics cross-check, install R on the host (for example, `brew install r` or
`sudo apt install r-base`).

See [`docs/demo.md`](docs/demo.md) for a detailed walkthrough of the scenario, what each step proves, and how to call the demo programmatically in tests.

## Documentation

- [`docs/system-overview.md`](docs/system-overview.md) — visual, diagram-first tour of the whole platform
- [`docs/architecture.md`](docs/architecture.md) — system architecture and module boundaries
- [`docs/data-model.md`](docs/data-model.md) — entities and relationships
- [`docs/execution-state-machine.md`](docs/execution-state-machine.md) — task execution lifecycle
- [`docs/security-model.md`](docs/security-model.md) — RBAC, secrets, least-privilege tools
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — single-node production deployment and recovery runbook
- [`docs/roadmap.md`](docs/roadmap.md) — the 8-phase build plan
- [`docs/assumptions.md`](docs/assumptions.md) — recorded architectural assumptions
- [`docs/governance/playbook/`](docs/governance/playbook/) — engineering governance playbook for gate workflow, reviews, Git procedure, and task packets
- [`docs/governance/knowledge/`](docs/governance/knowledge/) — institutional memory system, record templates, and knowledge records
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (ADRs)
- [`docs/governance/runtime/Runtime-Domain-Specification-v1.0.md`](docs/governance/runtime/Runtime-Domain-Specification-v1.0.md) — continuous Runtime Domain architecture baseline
- [`docs/agentic3/ARCHITECTURE-v2.md`](docs/agentic3/ARCHITECTURE-v2.md) — the canonical Agentic³ v2 architecture specification (the former governance/architecture integration skeleton is superseded and harvested into it)

## Status

**Phase 1** (monorepo, compose, backend + frontend scaffolding, DB/Redis/worker, migrations, health checks, lint/format, test framework) — **complete & verified**.

**Phase 2** (JWT auth + argon2, organizations, system + project RBAC planes, org-scoped repositories, secret resolution-by-reference + redaction, append-only audit events with app- and DB-level immutability) — **complete & verified** (backend **30/30** pytest, ruff + black clean, migrations render 0001→0002).

**Phase 3** (projects, requirements, milestones, tasks, dependencies with cycle rejection, risks, decisions, Kanban, CPM timeline + dependency graph, rule-based methodology recommender) — **complete & verified** (backend **56/56** pytest, ruff + black clean, migrations render 0001→0003).

**Phase 4** (agent registry, capability taxonomy, tool registry, default-deny agent-tool permissions, provider-neutral adapter with mock + Anthropic providers, capability-based matching + assignment) — **complete & verified** (backend **73/73** pytest, ruff + black clean, migrations render 0001→0004).

**Phase 5** (durable execution state machine, task dispatch, immutable execution records, retries/timeouts/escalation, reassignment, Celery `WorkflowEngine` engine) — **complete & verified** (backend **84/84** pytest, ruff + black clean, migrations render 0001→0005). A **GitHub Actions CI** workflow now applies migrations against real Postgres + smoke-tests `/readyz`.

**Phase 6** (deterministic evaluation rubrics, evaluator agents with enforced executor/evaluator separation, human approval gates, and the closed-loop remediation policy over the ten actions) — **complete & verified** (backend **102/102** pytest, ruff + black clean, migrations render 0001→0006).

**Phase 7** (project + agent metrics, a project dashboard with Gantt/dependency/risk-matrix/agent views, and CSV / JSON / Power BI-ready star-schema exports) — **complete & verified** (backend **112/112** pytest, frontend **14/14** vitest + tsc clean, migrations render 0001→0007).

**Phase 8** (security hardening, analysis workers, artifact storage, and the seeded **end-to-end demonstration** — objective → durable draft → explicit approval → one governed start → permissioned analysis → deterministic evaluation rejection → automatic remediation → acceptance-gated close) — **complete & verified**. The agent responses are deterministic `MockProvider` fixtures; pandas/matplotlib computation and artifact persistence are real.

**The original eight-phase MVP roadmap is implemented**, and the July 2026
remediation workstreams WS-1..WS-7 — culminating in the unchoreographed
objective-to-close loop proof (`tests/integration/test_objective_to_close.py`)
— are merged. The artifact/acceptance serialization boundary
([GitHub issue #45](https://github.com/AgentiCubed/A3/issues/45)) was closed by
making project closure atomic (PR #52, proof `test_atomic_close.py`). This is
not a claim that a live production environment exists. The July hardening
sequence through WS-8 now includes operator UI controls, halt/resume,
dependency-audit CI, live-provider proof, concurrency claims, and the
single-node production deployment contract in
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Live deployment and restore
rehearsal remain operator-run evidence, while the next strategic sequence is
Agentic³ Phase 0/1 in
[`docs/NEXT-STEPS-2026-07.md`](docs/NEXT-STEPS-2026-07.md). See
[`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md) and
[`docs/roadmap.md`](docs/roadmap.md) for the full record.
