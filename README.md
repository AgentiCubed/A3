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

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture and module boundaries
- [`docs/data-model.md`](docs/data-model.md) — entities and relationships
- [`docs/execution-state-machine.md`](docs/execution-state-machine.md) — task execution lifecycle
- [`docs/security-model.md`](docs/security-model.md) — RBAC, secrets, least-privilege tools
- [`docs/roadmap.md`](docs/roadmap.md) — the 8-phase build plan
- [`docs/assumptions.md`](docs/assumptions.md) — recorded architectural assumptions
- [`docs/public-showcase/`](docs/public-showcase/) — recruiter-safe public repo starter assets
- [`docs/decisions/`](docs/decisions/) — Architecture Decision Records (ADRs)

## Status

**Phase 1** (monorepo, compose, backend + frontend scaffolding, DB/Redis/worker, migrations, health checks, lint/format, test framework) — **complete & verified**.

**Phase 2** (JWT auth + argon2, organizations, system + project RBAC planes, org-scoped repositories, secret resolution-by-reference + redaction, append-only audit events with app- and DB-level immutability) — **complete & verified** (backend **30/30** pytest, ruff + black clean, migrations render 0001→0002).

**Phase 3** (projects, requirements, milestones, tasks, dependencies with cycle rejection, risks, decisions, Kanban, CPM timeline + dependency graph, rule-based methodology recommender) — **complete & verified** (backend **56/56** pytest, ruff + black clean, migrations render 0001→0003).

**Phase 4** (agent registry, capability taxonomy, tool registry, default-deny agent-tool permissions, provider-neutral adapter with mock + Anthropic providers, capability-based matching + assignment) — **complete & verified** (backend **73/73** pytest, ruff + black clean, migrations render 0001→0004).

**Phase 5** (durable execution state machine, task dispatch, immutable execution records, retries/timeouts/escalation, reassignment, Celery `WorkflowEngine` engine) — **complete & verified** (backend **84/84** pytest, ruff + black clean, migrations render 0001→0005). A **GitHub Actions CI** workflow now applies migrations against real Postgres + smoke-tests `/readyz`.

**Phase 6** (deterministic evaluation rubrics, evaluator agents with enforced executor/evaluator separation, human approval gates, and the closed-loop remediation policy over the ten actions) — **complete & verified** (backend **102/102** pytest, ruff + black clean, migrations render 0001→0006).

**Phase 7** (project + agent metrics, a project dashboard with Gantt/dependency/risk-matrix/agent views, and CSV / JSON / Power BI-ready star-schema exports) — **complete & verified** (backend **112/112** pytest, frontend **14/14** vitest + tsc clean, migrations render 0001→0007).

**Phase 8** (security hardening, real Python + R analysis workers, artifact storage, the seeded **end-to-end demonstration** — research → brief → data analysis → visualization → evaluation → deliberate failure → remediation → completion → closeout report, plus docs) — **complete & verified** (backend **120/120** pytest, frontend **14/14** vitest + tsc, ruff + black clean, migrations render 0001→0008).

**All eight phases are complete.** See **[`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md)** for the consolidated overview. Canonical host demo invocation is from repo root: `make demo` (see [`docs/demo.md`](docs/demo.md)). The [`docs/roadmap.md`](docs/roadmap.md) has the full phase-by-phase record; tracked follow-ups (all addressed) are in [`docs/issues/`](docs/issues/).
