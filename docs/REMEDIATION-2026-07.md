# Remediation Plan — July 2026 Audit Response

**Trigger:** external technical audit (2026-07-16, 714 lines) concluding:
real prototype, not as advertised — the claimed autonomous project loop is
largely unfinished. Showcase maturity 80–90%; claimed autonomous product
30–40%; production readiness 15–25%.

**Method:** every audit claim was re-verified against the code before
planning (§1). The plan decomposes the gap into workstreams with testable
definitions of done (§4), sequenced by dependency (§5). Enforcement is
CI tests, not prose — this document's own success criterion is that it
becomes redundant.

---

## 0. The essence

Strip it back to zero: the product promise is one sentence —
*give it an objective, and it runs the loop until acceptance criteria are
satisfied.* The codebase contains every **noun** that sentence needs
(projects, tasks, dependencies, agents, executions, evaluations,
remediations, approvals) and almost none of the **verbs** that connect
them. Data model ≈ done. Control flow ≈ missing. The audit's percentages
are two views of the same fact: the nouns score 80–90%, the verbs 30–40%.

The remediation is therefore not "fix ten bugs." It is: **build the verb
chain, one link at a time, each link proven by a test CI runs on every
commit.**

## 1. Verified claim register

Every claim was checked against code before this plan was written.

| # | Audit claim | Verification (code-level) | Status |
|---|------------|---------------------------|--------|
| 1 | Next.js 15.1.6 has a critical CVE; 15.1.9 patched | `package.json` pinned 15.1.6; registry shows 15.1.x line patched through 15.1.12 | **FIX IN COMPANION PR #31** — bumped to 15.1.12 there (latest same-minor patch); tests, tsc, production build, e2e all green on that branch. `main` still pins 15.1.6 until #31 merges |
| 2 | API execution bypasses Celery | `execute_task` calls `adapter.run()` inline (`execution_service.py:209`); `WorkflowEngine.submit_execution` is defined (`engines.py:30`) and **never called** from any service path | **CONFIRMED** |
| 3 | No objective-to-plan decomposition | `app/services/decomposition` named in `architecture.md` §4 **does not exist as a module at all** — worse than "unfinished," it is doc-drift | **CONFIRMED+** |
| 4 | No dependency-aware scheduler | Task completion does not trigger dispatch of newly-READY successors; dispatch is one-at-a-time via API call | **CONFIRMED** |
| 5 | No predecessor-output handoff | `build_prompt(task, extra_context)` exists; `extra_context` carries **remediation gaps** on retry (`:337`) but no path carries a predecessor's output into a successor's prompt | **CONFIRMED** (socket exists, nothing plugged in) |
| 6 | No functioning agent tool runtime | Tool registry + default-deny permissions exist; no `execute/run` path for a tool call anywhere in `app/orchestration` | **CONFIRMED** |
| 7 | Evaluator criticism does not determine the verdict | Nuanced: `combine_verdicts` takes the stricter of deterministic vs. agent verdict, so the agent verdict is *influential* — but it is parsed heuristically from free text (tracked issue 0004), and criticism (gaps) shapes only retry context, not the verdict itself | **PARTIALLY CONFIRMED** |
| 8 | Acceptance criteria do not control completion | `acceptance_criteria` stored on Project (`models/project.py:41`), **never read** by any evaluation or completion path | **CONFIRMED** |
| 9 | Demo recovery manually choreographed | `seed/demo.py` scripts the failure and the recovery | **CONFIRMED** |
| 10 | Security/concurrency/deploy/UI incomplete; governance stronger than enforcement | Accepted; itemized in WS-7/WS-8 | **ACCEPTED** |

## 2. First principles — the physical limit

The minimal irreducible loop the product claims:

```
objective → plan (tasks + dependencies)
         → schedule (dispatch READY work)
         → execute (agent + tools, durably, off the API thread)
         → handoff (outputs flow to successors)
         → evaluate (against acceptance criteria)
         → verdict (evaluation determines it)
         → remediate or complete
         → repeat until criteria satisfied or halted
```

Nothing less is "the autonomous loop." Everything else — dashboards,
exports, metrics, governance docs — is instrumentation *around* this chain
and cannot substitute for a missing link. Every workstream below is one
link; the loop works when the chain has no missing link, and only then.

## 3. What we can and cannot act on

**Can act now:** every gap in §1 is code we own. No external dependency
blocks any workstream. The CVE fix is delivered in companion PR #31.

**Cannot act on (park, don't churn):** the broader Agentic³ vision
(5–15%) is gated on design issues #16/#17 and Principal decisions on the
landed proposals — correctly sequenced as design-first, not a code gap.
Audit percentages themselves are calibration, not work items.

## 4. Workstreams

Each workstream states: what exists, what is missing, and a **definition
of done that is a CI-enforced test** — because the audit is right that our
documents outrun our enforcement.

### WS-1 — Execution spine (Celery for real)
*Clears claim 2. The foundation; everything else rides on it.*

- **Exists:** `CeleryWorkflowEngine`, worker container, immutable
  execution records, retries/timeouts in service logic.
- **Missing:** the API actually *using* it. Dispatch must become: API
  transitions task → QUEUED, calls `WorkflowEngine.submit_execution`,
  returns immediately; the **worker** runs `execute_task`. Add a
  settings-driven `sync` engine for tests so CI stays hermetic.
- **Done when:** an integration test proves dispatch returns before
  execution completes and the execution row is written by the worker path;
  CI includes one real end-to-end dispatch through Celery against Redis
  (the CI services already exist).
- **Status: DELIVERED — merged to `main` in PR #34 (2026-07-17).** Proof:
  `tests/integration/test_dispatch_spine.py` (hermetic acceptance: dispatch
  returns with the task QUEUED and zero execution rows; the worker
  entrypoint then completes it with the exact captured params) and
  `tests/integration/test_celery_broker_smoke.py` + the CI "Celery spine
  smoke" step (HTTP dispatch → real Redis → real worker subprocess → real
  Postgres → polled completion). Compose api sets
  `WORKFLOW_ENGINE_BACKEND=celery`; inline remains the dev/test default,
  returning the full result as before. Found-and-fixed along the way: the
  deployed worker never registered `execution.run` at boot (`celery_app`
  lacked `include=["app.workers.tasks"]`), so the pre-existing worker
  container could never have executed a task message — a candidate Failure
  Record for the knowledge system.

### WS-2 — Dependency-aware scheduler
*Clears claim 4. Turns one-shot dispatch into a loop.*

- **Exists:** DAG with cycle rejection; READY-state logic; the new
  EventBus (task-transition events are already published).
- **Missing:** a scheduler that reacts to `task.transition → COMPLETED`
  by computing newly-READY successors and dispatching them (WS-1 path),
  with a project-level concurrency cap and a halt switch.
- **Done when:** a seeded 3-task chain (A→B→C) completes end-to-end from
  a single "start project" call in an integration test, with no per-task
  API calls.
- **Status: DELIVERED — merged to `main` in PR #36 (2026-07-17).** Proof:
  `tests/integration/test_scheduler.py` — the definition-of-done test is
  `test_inline_start_completes_full_chain_in_one_call` (single
  `POST /projects/{id}/start`, dependency order proven by execution
  timestamps); worker-driven chain advancement, the concurrency cap, and
  unschedulable-predecessor gating are each covered. The compose worker
  sets `WORKFLOW_ENGINE_BACKEND=celery` and `EVENT_BUS_BACKEND=redis`.

### WS-3 — Predecessor-output handoff
*Clears claim 5.*

- **Exists:** `extra_context` socket; artifact store; execution outputs
  persisted.
- **Missing:** on dispatch, collect completed predecessors' outputs
  (bounded: latest successful execution output per predecessor, truncated
  by budget) and inject via the existing socket; record what was injected
  in `input_context` for audit.
- **Done when:** integration test asserts B's prompt contains A's output
  and the injection is recorded on B's execution row.
- **Status: DELIVERED — merged to `main` in PR #38 (2026-07-17).** Proof:
  `tests/integration/test_handoff.py` — the definition-of-done test is
  `test_predecessor_output_lands_in_successor_prompt_and_is_recorded`;
  budget truncation, multi-predecessor budget sharing, incomplete
  predecessors, and latest-successful selection are each covered. Budget
  is the `handoff_budget_chars` setting.

### WS-4 — Verdict and acceptance-criteria integrity
*Clears claims 7 and 8. Makes evaluation mean something.*

- **Exists:** rubric engine, stricter-of-two verdict combination,
  executor/evaluator separation, `acceptance_criteria` stored.
- **Missing:** (a) structured evaluator output — the evaluator agent
  returns a JSON verdict contract instead of heuristically-parsed prose
  (closes tracked issue 0004); (b) acceptance criteria compiled into
  rubric criteria at project level, so **completion is gated by them**:
  a project cannot reach COMPLETED while criteria-derived rubrics fail.
- **Done when:** tests prove (a) a malformed evaluator response fails
  closed (NEEDS_REVISION, never silent PASS), and (b) a project with an
  unsatisfied acceptance criterion cannot complete.
- **Status: DELIVERED in three merged PRs.** (a) PR #39 (2026-07-17):
  `verdict_json_v1` contract with fail-closed parsing — proof:
  `tests/unit/test_verdict_combination.py` and the fail-closed integration
  tests in `tests/integration/test_evaluation.py`; closes the issue 0004
  residual. (b) PR #41 (2026-07-18): acceptance-criteria gate on project
  close — proof: `tests/integration/test_acceptance_gate.py`
  (`test_close_refused_until_rubric_criterion_met` is the
  definition-of-done test; acknowledged abandonment is audited).
  Hardened by PR #42 (2026-07-18): evaluation-rejected outputs excluded
  from the acceptance corpus, criteria shapes validated at creation,
  malformed persisted criteria fail closed — the contract WS-6 will
  generate against.

### WS-5 — Agent tool runtime
*Clears claim 6.*

- **Exists:** tool registry, sensitivity levels, default-deny agent-tool
  permissions, `ToolSchema`/`ToolCall` in the adapter contract.
- **Missing:** the runtime loop — when `adapter.run` returns tool calls:
  check permission (deny = halt + audit), execute against an allowlisted
  tool implementation table, append results, re-invoke, bounded by
  iteration and time budgets. Start with two real tools (artifact
  read/write; the existing Python analysis worker) — enough to prove the
  seam without opening arbitrary execution.
- **Done when:** tests prove a permitted tool round-trip works, a denied
  tool call halts with an audit event, and budgets terminate runaway
  loops.
- **Status: DELIVERED — merged to `main` in PR #40 (2026-07-17).** Proof:
  `tests/integration/test_tool_runtime.py` — permitted round-trip creates
  a real artifact with a `tool.invoked` audit; ungranted, unknown, and
  registered-but-unimplemented calls halt BLOCKED with `tool.denied`
  audits and no side effects; `[[TOOL_LOOP]]` termination proves the
  iteration budget; artifact reads are project-scoped.

### WS-6 — Objective-to-plan decomposition
*Clears claim 3. The front door — deliberately LAST of the loop links.*

- **Exists:** nothing (module absent; fix `architecture.md` §4 in this
  PR's follow-up or mark it planned).
- **Missing:** `services/decomposition`: objective → proposed tasks +
  dependencies + per-task acceptance criteria via the AgentAdapter,
  landing as a **draft plan behind a human approval gate** (Constitution
  Art. VI §4: acceptance conditions before execution). Mock-provider
  deterministic output makes it testable.
- **Done when:** integration test: objective in → approved plan →
  WS-2 scheduler runs it → project completes against generated criteria.
  This test **is** the product claim, in CI, unchoreographed.
- **Status: DELIVERED — merged to `main` in PRs #47, #48, #49 (2026-07-18).**
  Proof: `tests/integration/test_decomposition.py` (objective → fail-closed
  `plan_json_v1` draft), `test_plan_approval.py` (draft → audited human
  approve/reject; rejection leaves no executable residue),
  `test_plan_runtime.py` + `test_plan_history_gate.py` +
  `test_persisted_task_rubrics.py` (approved plan materializes through
  `task_service` and runs through the WS-2 scheduler against the *generated*
  criteria). Implementation: `services/decomposition_service.py`,
  `api/v1/routers/plans.py`, `models/decomposition_plan.py` — the
  `architecture.md` decomposition reference is now true (claim 3 cleared).

### WS-7 — Honest demo and loop-level CI
*Clears claim 9; the proof that clears the "as advertised" verdict.*

- Replace the choreographed demo recovery with the real loop: seed
  objective, let WS-2..6 run it with the mock provider, including one
  genuine failure remediated by the remediation policy without scripted
  rescue. Promote to a CI job. Delete the choreography.
- **Status: DELIVERED — merged to `main` in PRs #49, #50, #51 (2026-07-18).**
  Proof: `tests/integration/test_objective_to_close.py` (unchoreographed
  objective → plan → approval → scheduled execution → evaluation-driven
  remediation → acceptance-gated close) and `test_demo.py`, which CI runs as
  the named **Governed objective-to-close proof** step. Post-baseline
  follow-up: project closure made atomic against concurrent execution and
  artifact writes in PR #52 (issue #45), proof `test_atomic_close.py`.

### WS-8 — Hardening ledger (security, concurrency, deploy, UI)
*Clears claims 1 and 10 progressively.*

- CVE bump **done** (15.1.12). Remaining, tracked as a living checklist:
  dependency-audit job in CI (`npm audit`/`pip-audit`, fail on critical),
  optimistic-locking review on task transitions under WS-2 concurrency,
  deployment story past compose (out of scope until WS-1..6 land), UI
  write-paths (approve/reject, dispatch, halt) so the dashboard stops
  being read-only.
- **Status: OPEN — the only remaining workstream.** WS-1..WS-7 have all
  merged, so the WS-8 checklist (plus the project-level halt switch WS-2
  deferred) is now the gap between "loop proven in CI" and "completed
  product." The verified gap register and recommended sequencing live in
  `docs/NEXT-STEPS-2026-07.md` (2026-07-19).

## 5. Sequence and why

```
WS-1 (spine)  ──►  WS-2 (scheduler) ──►  WS-6 (decomposition)
   │                    │                      │
   ├──►  WS-3 (handoff, needs spine)           │
   ├──►  WS-5 (tool runtime, needs spine)      ▼
   └──►  WS-4 (verdict/criteria, parallel) ─► WS-7 (honest demo = proof)
                                        WS-8 continuous
```

- **WS-1 first** because a scheduler dispatching inline API executions
  would multiply the central dishonesty, not fix it.
- **WS-4 in parallel** — it touches evaluation, not the spine.
- **WS-6 last of the links** because generated plans are only meaningful
  once execution, handoff, and criteria-gated completion actually work;
  building the front door before the house repeats the original mistake.
- **WS-7 is the finish line**: the audit's "as advertised" verdict flips
  exactly when the unchoreographed loop test is green in CI, and not
  before.

## 6. What this plan deliberately does not do

- No production-deployment work before the loop exists (sequencing, not
  neglect).
- No new governance documents — the audit says enforcement lags the
  paperwork; this plan adds tests, not prose, and the ARCHITECTURE-v2
  workstream continues separately under issues #16/#17/#19.
- No relitigating the audit's percentages — they are calibration, and
  the register in §1 shows they were substantially earned.

## 7. Standing rule adopted from this audit

Every future capability claim in README/docs must cite the CI test that
proves it. A claim without a test is marked *(planned)*. This rule applies
retroactively to the Phase 1–8 status section in the README as WS-7 lands.
