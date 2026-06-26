# AgentiCubed — Build Roadmap

Eight phases. Each phase ends with: run tests → fix failures → update docs →
list completed acceptance criteria → record remaining technical debt. Phases are
implemented one at a time.

## Phase 1 — Foundation *(complete)*
Monorepo, Docker Compose, backend skeleton, frontend skeleton, PostgreSQL,
Redis, Celery worker, Alembic migrations, `.env.example`, health checks,
linting, formatting, test frameworks.

**Acceptance criteria**
- [~] `docker compose up` starts db, redis, api, worker, frontend. *(compose
  manifest complete and service-correct; full `up` not yet run in this
  environment — Docker not exercised locally. Tracked in `docs/issues/0001`.)*
- [x] `GET /healthz` (liveness) returns 200 — verified via `TestClient`.
  `/readyz` (db+redis) implemented; its 200 path requires live db+redis (Docker).
- [~] Alembic baseline migration present and importable; clean apply against a
  live Postgres not yet run locally (Docker). Tracked in `docs/issues/0001`.
- [x] `ruff` + `black` (backend) configured and **passing**; `eslint` (frontend)
  configured. *(Prettier deferred — Next/ESLint covers formatting for now;
  noted in `docs/issues/0002`.)*
- [x] `pytest` (backend 3 passing) and `vitest` (frontend 5 passing) run green.
- [x] CI-style `make check` target runs lint + tests.

**Verification (run 2026-06-25, local, Python 3.12 + Node 26):**
- `pytest` → `3 passed`
- `ruff check app` → `All checks passed!` · `black --check app` → clean
- `vitest run` → `5 passed (2 files)`
- `tsc --noEmit` → exit 0

## Phase 2 — Identity, RBAC, audit *(complete)*
Authentication, organizations, project roles, role-based permissions, secure
configuration handling, audit events.

**Acceptance criteria**
- [x] Register/login issues JWT (access + refresh); passwords hashed with argon2
  (`app/core/security.py`). Verified by `test_auth_flow` + `test_security`.
- [x] Org scoping enforced at repository layer (`OrgScopedRepository`,
  `app/db/repository.py`). Verified by `test_org_scoping` (cross-org → 404).
- [x] `authorize()` guard with system + project role planes (`app/core/rbac.py`),
  incl. the agent-cannot-escalate hard rule. Verified by `test_rbac`.
- [x] Secrets resolved by reference (`app/core/secrets.py`); recursive redaction
  on audit before/after and logs (`app/core/redaction.py`). Verified by
  `test_redaction` + `test_audit_and_immutability::test_secret_redacted...`.
- [x] Material changes emit `AuditEvent`; immutability enforced in the app
  (session `before_flush` guard) **and** in the DB (Postgres UPDATE/DELETE
  trigger in migration `0002`). Verified by `test_audit_and_immutability`.

**Verification (run 2026-06-25, local):**
- `pytest` → `30 passed` · `ruff` + `black --check` → clean
- `alembic upgrade head --sql` renders 0001→0002 cleanly (tables, indexes,
  immutability trigger). Live apply against Postgres still tracked in issue 0001.

**Phase-2 design notes:**
- Login is by email + password. Email is unique per org *and* (for MVP) globally,
  so login needs no org selector. See `docs/assumptions.md`.
- `project_members` exists now (project-role plane is testable), but its FK to
  `projects` is deferred to Phase 3 when that table lands.

## Phase 3 — Projects & planning domain *(complete)*
Projects, requirements, milestones, tasks, dependencies, risks, decisions,
Kanban workflow, timeline, critical-path calculation.

**Acceptance criteria**
- [x] CRUD for project/requirement/milestone/task/risk/decision (`projects`
  router + `project_service`/`task_service`). Org-scoped, audited mutations.
- [x] Dependency creation rejects self-loops, duplicates, and cycles
  (`app/scheduling/graph.py` DFS/Kahn; service builds the proposed graph and
  rejects → HTTP 409 with the offending cycle). Verified by `test_projects` +
  `test_graph`.
- [x] Kanban board transitions (`PATCH .../tasks/{id}/kanban`, audited).
- [x] CPM computes ES/EF/LS/LF + slack + critical path
  (`app/scheduling/critical_path.py`). Verified by `test_critical_path` (classic
  diamond, lag, parallel) and end-to-end via `/timeline` + `/graph`.
- [x] Bonus: rule-based methodology recommender (Module 2) wired into project
  creation. Verified by `test_methodology`.

**Verification (run 2026-06-25, local):**
- `pytest` → `56 passed` · `ruff` + `black --check` → clean
- `alembic upgrade head --sql` renders 0001→0003 cleanly (incl. the
  `project_members→projects` FK that resolves assumption A17).

**Phase-3 notes:**
- CPM models all dependency types as finish-to-start for the MVP; the field is
  stored and surfaced but SS/FF/SF schedule as FS. Tracked in `docs/issues/0003`.
- System-plane RBAC is enforced on mutations; project-plane role resolution
  (e.g. a `manager` who isn't an org admin) lands with agents in Phase 4 (A18).

## Phase 4 — Agents, capabilities, matching *(complete)*
Agent registry, capability taxonomy, tool registry, agent-tool permissions,
provider-neutral adapter, agent matching.

**Acceptance criteria**
- [x] `AgentAdapter` port + `MockProvider` (deterministic) + a real provider
  (`AnthropicProvider`), selected by name via the registry (ADR-0003). The real
  adapter resolves its credential by reference *before* any network call.
  Verified by `test_providers`.
- [x] Curated capability taxonomy (`app/core/capabilities.py`); agent capability
  declarations validated against it (unknown → 422). Verified by `test_agents`.
- [x] Tool registry + default-deny `AgentToolPermission` (row existence = grant;
  expiry-aware `has_permission`). Verified by `test_agents`.
- [x] Capability-based matching ranks eligible (active + full-cover) agents ahead
  of partial matches, then by coverage and proficiency (`app/services/matching`).
  Verified by `test_matching` + `/agents/matches`.
- [x] Bonus: capability-checked task→agent assignment (422 on mismatch); the
  agent self-escalation block is enforced at the service layer and tested.

**Verification (run 2026-06-25, local):**
- `pytest` → `73 passed` · `ruff` + `black --check` → clean
- `alembic upgrade head --sql` renders 0001→0004 cleanly (incl. the deferred
  `tasks.assigned_agent_id → agents` FK).

**Phase-4 notes:**
- New RBAC actions `AGENT_MANAGE` / `TOOL_MANAGE` (owner/admin system, manager
  project plane); agents remain hard-denied every management action.
- High-sensitivity tools carry a `sensitivity` flag; the approval gate that
  blocks their invocation lands in Phase 6. `has_permission` is wired for the
  Phase-5 dispatcher.

## Phase 5 — Dispatch & execution *(complete)*
Task dispatch, execution records, background workers, retries, timeouts,
reassignment, human escalation, execution state machine.

**Acceptance criteria**
- [x] State machine enforces legal transitions; every transition is audited and
  illegal ones raise `IllegalTransition` (`app/orchestration/state_machine/`).
  Verified by `test_state_machine` + execution flow tests.
- [x] Worker runs an execution end-to-end via the engine port
  (`CeleryWorkflowEngine` implements `WorkflowEngine`; eager-mode test runs the
  full `execute_task` through `submit_execution`). Verified by
  `test_execution::test_worker_runs_execution_via_engine_port`.
- [x] Retry + timeout + reassignment exercised by tests (mock provider `[[FAIL]]`
  / `[[SLEEP:n]]` markers drive deterministic failure/timeout; escalation →
  BLOCKED; reassignment → READY). Verified by `test_execution`.
- [x] Immutable `TaskExecution` per attempt (app guard + Postgres trigger in
  migration 0005). Verified by `test_execution::test_task_execution_is_immutable`.

**Verification (run 2026-06-25, local):**
- `pytest` → `84 passed` · `ruff` + `black --check` → clean
- `alembic upgrade head --sql` renders 0001→0005 cleanly (incl. the execution
  immutability trigger).
- **CI added** (`.github/workflows/ci.yml`): applies migrations to real Postgres
  16 + runs a `/readyz` smoke test (db + redis) — mitigates issue 0001.

**Phase-5 notes:**
- Inline execution (`execute_task`) is the unit of work the API calls directly;
  the Celery engine runs that same function in a worker. Temporal would implement
  the same `WorkflowEngine` port (ADR-0002).
- A successful run currently transitions RUNNING→COMPLETED; Phase 6 interposes
  EVALUATING (the machine already permits RUNNING→EVALUATING→COMPLETED).
- The Celery worker path is verified in eager mode; a live broker run needs Redis
  (Docker/CI), tracked alongside issue 0001.

## Phase 6 — Evaluation & remediation
Evaluation rubrics, deterministic validation, evaluator agents, human approvals,
revision requests, closed-loop remediation.

**Acceptance criteria**
- [ ] Deterministic validators + evaluator-agent path produce `Evaluation`.
- [ ] Executor/evaluator separation enforced.
- [ ] Remediation policy selects + records action and justification.
- [ ] Approval gate blocks irreversible actions.

## Phase 7 — Analytics & visualization
Dashboards, Gantt, dependency views, risk matrices, project metrics, agent
metrics, CSV export, JSON export, Power BI-ready exports.

**Acceptance criteria**
- [ ] Project + agent metrics computed and persisted.
- [ ] Gantt + dependency graph + risk matrix render in UI.
- [ ] CSV / JSON / Power BI-compatible exports.

## Phase 8 — Hardening & demonstration
Comprehensive testing, security hardening, documentation, seed data, end-to-end
demonstration project.

**Acceptance criteria**
- [ ] E2E demo: research → brief → data analysis → visualization → evaluation →
      deliberate failure → remediation → completion → closeout report.
- [ ] Security review checklist passed.
- [ ] Seed data + docs complete.

## Incomplete-requirement policy
A requirement that cannot be completed is **not** silently dropped. It is logged
as a documented issue in `docs/issues/` stating: what is incomplete, why, the
proposed implementation, dependencies, and security implications.
