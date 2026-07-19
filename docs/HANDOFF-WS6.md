# Handoff brief — WS-6: Objective-to-plan decomposition

**Record type:** executor handoff brief. Written so that any executor — human
or AI assistant — can implement WS-6 from repository artifacts alone, with no
conversational memory required. Every capability claim below cites the test
that proves it, per the standing rule in `docs/REMEDIATION-2026-07.md` §7:
*"The repository proves it. A claim without a test is marked (planned)."*

**Authoritative spec:** `docs/REMEDIATION-2026-07.md`, section *WS-6 —
Objective-to-plan decomposition*. This brief summarizes and points; where the
two disagree, the remediation plan wins.

---

## 1. What WS-6 is

From the remediation plan, verbatim:

> **Missing:** `services/decomposition`: objective → proposed tasks +
> dependencies + per-task acceptance criteria via the AgentAdapter, landing as
> a **draft plan behind a human approval gate** (Constitution Art. VI §4:
> acceptance conditions before execution). Mock-provider deterministic output
> makes it testable.
>
> **Done when:** integration test: objective in → approved plan → WS-2
> scheduler runs it → project completes against generated criteria. This test
> **is** the product claim, in CI, unchoreographed.

WS-6 is the last link of the loop: everything downstream of a plan already
exists and is CI-proven (section 2). WS-6 supplies the plan itself.

Note: `docs/architecture.md` names a decomposition service that does not yet
exist in code (audit claim 3). The WS-6 spec instructs the implementer to
either make that reference true or mark it planned.

## 2. Machinery already on `main` that WS-6 plugs into

| Capability | Where | Proven by |
| --- | --- | --- |
| Async dispatch through the `WorkflowEngine` port; worker executes with caller's exact params | `execution_service`, `workers/tasks.py`, `orchestration/engines.py` | `tests/integration/test_dispatch_spine.py`; real-broker smoke `test_celery_broker_smoke.py` (CI job "Celery spine smoke") |
| Dependency-aware scheduling: one `POST /projects/{id}/start` runs a whole chain; worker advances successors | `services/scheduler_service.py` | `tests/integration/test_scheduler.py` (incl. inline A→B→C acceptance test) |
| Predecessor-output handoff into successor prompts, budgeted and audited | `execution_service.collect_predecessor_context` | `tests/integration/test_handoff.py` |
| Structured evaluator verdicts, fail-closed (`verdict_json_v1`) | `services/evaluation_service.py` | `tests/unit/test_verdict_combination.py`, `tests/integration/test_evaluation.py` |
| Acceptance-criteria gate on project close (409 until met; acknowledged abandonment audited) | `services/acceptance_service.py`, `services/closeout_service.py` | `tests/integration/test_acceptance_gate.py` |
| Agent tool runtime: default-deny permissions, server-side allowlist, budgets | `services/tool_runtime.py` | `tests/integration/test_tool_runtime.py` |

WS-6's definition-of-done test composes these: the generated plan's tasks run
through the WS-2 scheduler, hand results forward via WS-3, and the project
closes through the WS-4b gate against the *generated* criteria.

## 3. Prerequisite: PR #42 — **satisfied (merged 2026-07-18)**

PR #42 (`fix acceptance gate integrity`) hardened the acceptance-criteria
contract — evaluation-rejected outputs are excluded from the acceptance
corpus, criteria shapes are validated at creation (typed `AcceptanceCriteriaIn`
schema on `ProjectCreate`), and malformed persisted criteria fail closed. Its
rationale stated the dependency: *"WS-6 will generate these specifications, so
the contract must be trustworthy before decomposition lands."*

It is on `main`; WS-6 is unblocked. The criteria WS-6 generates must satisfy
`acceptance_service._malformed_spec_reason` and the creation-time schema
validation, or the plan must be rejected at generation time.

## 4. Suggested implementation shape *(planned — nothing below exists yet)*

These are recommendations from the WS-1..WS-5 implementer, consistent with the
established patterns; the executor may deviate where the spec permits.

- **Module:** `backend/app/services/decomposition_service.py`, called from a
  new router endpoint (e.g. `POST /projects/{id}/plan`). Domain logic in the
  service; the router stays thin (existing convention throughout
  `app/api/v1/routers/`).
- **Structured plan contract:** follow the WS-4a pattern exactly — define a
  versioned JSON contract (e.g. `plan_json_v1`: tasks with title /
  description / estimate / required capabilities, dependency edges by index,
  per-task acceptance criteria in the rubric-spec shape from
  `app/evaluation/rubric.py`), request it via `AgentRunRequest.params`,
  and parse **fail-closed**: malformed planner output must never silently
  become an executable plan. Precedent: `parse_evaluator_verdict` in
  `evaluation_service.py`.
- **Deterministic mock:** extend `MockProvider` with a `plan_json_v1` branch
  (precedent: its `verdict_json_v1` branch and `[[TOOL:...]]` markers), so the
  definition-of-done test runs hermetically with no live provider
  (assumption A15).
- **Human approval gate:** the generated plan lands as a *draft proposal* —
  no tasks dispatched, nothing QUEUED — and requires an explicit human
  approval action before tasks/dependencies are materialized. Reuse the
  existing `Approval` model and decision flow if it fits; otherwise a
  dedicated plan-approval entity with the same audited approve/reject shape.
  On approval, materialize tasks + dependencies through the existing
  `task_service` (which cycle-checks), then the existing `POST /start` runs
  the project. Rejection must leave no executable residue.
- **Validation before approval is even offered:** generated dependencies must
  pass the existing cycle check; generated criteria must pass #42's shape
  validation. A plan that fails validation is rejected at generation time,
  audited, and never shown as approvable.
- **Audit everything:** plan proposed / approved / rejected as audit events
  with `project_id`, following `record_audit` conventions (events also feed
  the live SSE stream).

## 5. Conventions binding any executor

These apply regardless of which assistant or human does the work:

1. **Focused PRs off `main`, opened as drafts.** The Principal promotes and
   merges. One workstream per PR (established via the PR #29 split directive).
2. **Claims cite tests.** Any capability statement in docs or PR bodies cites
   the CI test proving it, or is marked *(planned)*
   (`docs/REMEDIATION-2026-07.md` §7).
3. **Progress credit only for merged default-branch work.** Open/draft PRs and
   green CI alone earn no official progress (Principal's standing scoring
   rule).
4. **Hermetic CI.** Deterministic tests never call a live provider
   (assumption A15); use `MockProvider` and adapter doubles.
5. **Gates:** `ruff check`, `black --check`, and the full backend suite green
   before push. CI runs backend, frontend, e2e, compose, and the Celery
   broker smoke.
6. **Governance docs carry provenance labels** (`[supported: source]` /
   `[reconstructed]` / `[proposed]`) per the Principal's review directive on
   PR #29 and the merged concept docs.

## 6. Test harness pointers

- `backend/tests/conftest.py`: file-backed SQLite, `TestSessionFactory`,
  overridden `db_session`, sync `client` fixture.
- Helper patterns (auth/project/task/agent/assign/dispatch/dependency) are
  copy-adaptable from `tests/integration/test_scheduler.py` and
  `test_acceptance_gate.py`.
- Worker-path testing: `workers.tasks.set_session_factory(TestSessionFactory)`
  runs the real worker entrypoint against the test DB (see
  `test_scheduler.py::test_worker_completion_advances_chain_to_the_end`).
- Adapter doubles: `monkeypatch.setattr(execution_service, "get_adapter", ...)`
  for the executor path; `evaluation_service.get_adapter` for the judge path.
- `MockProvider` control markers are documented in its module docstring
  (`[[FAIL]]`, `[[SLEEP:s]]`, `[[TOOL:...]]`, `[[TOOL_LOOP:...]]`,
  `[[MALFORMED]]` in reviewed output).

## 7. Known stale spots (do not inherit as fact)

- `docs/architecture.md`'s decomposition reference remains aspirational until
  WS-6 lands (see section 1).
