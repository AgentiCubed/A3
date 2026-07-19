# AgentiCubed — Project Summary

A consolidated overview of the delivered platform. For depth, see
[`architecture`](architecture.md), [`data-model`](data-model.md),
[`execution-state-machine`](execution-state-machine.md),
[`security-model`](security-model.md), [`roadmap`](roadmap.md), and
[`demo`](demo.md).

## What it is

AgentiCubed converts a project objective into a durable draft plan, waits for
explicit approval of the exact plan, materializes the approved graph and agent
policies, executes tasks, evaluates outputs, detects failures, applies bounded
closed-loop remediation, and closes only when acceptance evidence passes —
running the control loop:

```
Plan → Assign → Execute → Evaluate → Identify Gaps → Remediate → Re-execute
```

## Status: original 8-phase MVP baseline implemented

"Green" below means the phase-level acceptance evidence exists. It does not
mean every production-hardening or scale concern has been eliminated.

| Phase | Scope | Verification |
|---|---|---|
| 1 | Monorepo, Docker Compose, backend/frontend skeletons, DB/Redis/worker, migrations, health, lint/format, tests | green |
| 2 | JWT auth + argon2, orgs, system + project RBAC, org-scoped repos, secrets-by-reference + redaction, append-only audit | green |
| 3 | Projects, requirements, milestones, tasks, dependencies (cycle-rejected), risks, decisions, Kanban, **multi-relation CPM** | green |
| 4 | Agent registry, capability taxonomy, tool registry, default-deny permissions, provider adapters (mock + Anthropic), matching | green |
| 5 | Durable execution state machine, dispatch, immutable executions, retries/timeouts/escalation, reassignment, Celery `WorkflowEngine` | green |
| 6 | Deterministic rubrics + evaluator agents (separation enforced + influential verdict), approvals, closed-loop remediation | green |
| 7 | Project + agent metrics, dashboard (Gantt/dependency/risk matrix/agent table), CSV/JSON/Power BI exports | green |
| 8 | Security hardening, **real** Python + R analysis workers, artifacts, seeded **end-to-end demo**, docs | green |

## Verification at a glance

- **Backend:** full pytest, Ruff, and Black checks run in CI
- **Frontend:** Vitest, typecheck, ESLint, and Prettier checks run in CI
- **Migrations:** `alembic upgrade head` renders 0001→0008 cleanly (verified
  against real Postgres in CI)
- **CI** (`.github/workflows/ci.yml`): backend against real Postgres 16 + Redis 7
  (migrate + `/readyz` smoke), frontend (format/typecheck/lint/test), and a
  `docker compose config` validation job
- **Demo** (`make demo`): objective → durable draft → exact explicit approval →
  one governed start → permissioned real pandas analysis → evaluation-driven
  automatic remediation → artifact and acceptance gates → evidence-bound close.
  Planning and agent text are deterministic fixtures; R is an optional cross-check.

## Requirements coverage

- **23 data entities** — all implemented (Organization, User, Project,
  ProjectMethodology, ProjectRequirement, Milestone, Task, TaskDependency,
  TaskExecution, Agent, AgentCapability, Tool, AgentToolPermission, Evaluation,
  EvaluationCriterion, Approval, Risk, Decision, Artifact, AuditEvent,
  ProjectMetric, AgentMetric, PromptTemplate).
- **10 execution states** + a durable transition machine that audits every
  transition and rejects illegal ones.
- **13 modules** — intake, methodology, decomposition, capability, agent registry,
  matching, orchestration, evaluation, remediation, approval, governance,
  analytics, closeout.
- **Closed-loop remediation** — a policy selects one of the ten actions and
  records the action + justification; auto-applicable actions re-execute, the
  rest escalate to a human gate.

## Architectural guarantees

- Provider-neutral agent adapters; orchestration never imports a vendor SDK.
- Project logic, orchestration, provider integrations, and UI are separated.
- Every execution and evaluation is stored; execution/evaluation/audit history is
  **immutable** (app-layer guard + Postgres triggers).
- RBAC (two planes), least-privilege default-deny tool permissions, and a
  three-layer block preventing agents from escalating their own permissions.
- Executor ≠ evaluator (enforced). Human approval gates before irreversible or
  sensitive actions. Secrets are referenced by env key, never inlined or logged.
- Worker layer behind a `WorkflowEngine` port so Temporal can replace Celery
  without touching domain logic.

## Security posture

argon2 password hashing · short-lived JWT access + refresh · org isolation at the
repository layer · default-deny tool permissions with expiry · secret redaction on
logs and audit payloads · response security headers (CSP, X-Frame-Options,
nosniff, no-referrer) · CORS config · a startup guard refusing the insecure
default `SECRET_KEY` in production · httpOnly session cookie for the dashboard.

## How to run

```bash
cp .env.example .env
make up            # Postgres, Redis, API, worker, web
make migrate       # apply migrations
make demo          # run the end-to-end demonstration
make check         # backend + frontend lint and tests
```

API docs: `http://localhost:8000/docs` · Web: `http://localhost:3000` ·
Sign in at `/login`, dashboards at `/projects/<id>`.

## Original roadmap follow-ups

| Issue | Outcome |
|---|---|
| 0001 Docker stack | **Resolved via CI** (migrate + readyz against real PG/Redis; compose validated) |
| 0002 Prettier / ESLint flat config | **Resolved** (Prettier wired + CI); flat-config migration deferred (cosmetic) |
| 0003 CPM dependency types | **Resolved** (all four PMI relations implemented + tested) |
| 0004 Evaluator-agent verdict | **Resolved** (agent verdict now influential; can downgrade, never upgrade a hard fail) |
| 0005 Charts + dashboard auth | **Auth resolved** (httpOnly session cookie); richer charts deferred per ADR-0005 |

Architecture substitutions are recorded as ADRs (0001–0005) in
[`decisions/`](decisions/).

Post-baseline hardening is tracked separately. In particular, concurrent artifact
writes versus acceptance snapshots remain open in
[GitHub issue #45](https://github.com/AgentiCubed/A3/issues/45).
