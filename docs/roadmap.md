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

## Phase 2 — Identity, RBAC, audit
Authentication, organizations, project roles, role-based permissions, secure
configuration handling, audit events.

**Acceptance criteria**
- [ ] Register/login issues JWT; passwords hashed with argon2.
- [ ] Org scoping enforced at repository layer.
- [ ] `authorize()` guard with system + project role planes.
- [ ] Secrets resolved by reference; redaction filter on logs/audit.
- [ ] Material changes emit `AuditEvent`; immutability guards in DB.

## Phase 3 — Projects & planning domain
Projects, requirements, milestones, tasks, dependencies, risks, decisions,
Kanban workflow, timeline, critical-path calculation.

**Acceptance criteria**
- [ ] CRUD for project/requirement/milestone/task/risk/decision.
- [ ] Dependency creation rejects cycles.
- [ ] Kanban board state transitions.
- [ ] CPM computes earliest/latest start/finish + critical path.

## Phase 4 — Agents, capabilities, matching
Agent registry, capability taxonomy, tool registry, agent-tool permissions,
provider-neutral adapter, agent matching.

**Acceptance criteria**
- [ ] `AgentAdapter` port + `MockProvider` + one real provider.
- [ ] Capability taxonomy + agent capability declarations.
- [ ] Tool registry + default-deny `AgentToolPermission`.
- [ ] Matching ranks agents by required capabilities.

## Phase 5 — Dispatch & execution
Task dispatch, execution records, background workers, retries, timeouts,
reassignment, human escalation, execution state machine.

**Acceptance criteria**
- [ ] State machine table enforces legal transitions; illegal ones audited.
- [ ] Worker runs an execution end-to-end via the engine port.
- [ ] Retry + timeout + reassignment paths exercised by tests.
- [ ] Immutable `TaskExecution` per attempt.

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
