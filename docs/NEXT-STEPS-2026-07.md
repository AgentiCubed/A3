# Next Steps to Product Completion — 2026-07-19 assessment

**Record type:** planning assessment. Written against the repository state at
commit `3f71045` (2026-07-18) after re-verifying every status claim against
code, tests, CI configuration, and the GitHub issue/PR trackers, per the
standing rule in `docs/REMEDIATION-2026-07.md` §7: *"The repository proves it.
A claim without a test is marked (planned)."*

**Purpose:** answer one question — *what work remains between the current
state and a completed product, and in what order should it be done?*

---

## 1. Where the product stands (verified)

The July 2026 remediation plan is substantially **complete**. Every loop link
it defined has merged to `main` with CI-enforced proof:

| Workstream | Delivered by | Proof (in CI) |
| --- | --- | --- |
| WS-1 Execution spine | PR #34 | `test_dispatch_spine.py`, `test_celery_broker_smoke.py` (CI "Celery spine smoke") |
| WS-2 Dependency-aware scheduler | PR #36 | `test_scheduler.py` |
| WS-3 Predecessor-output handoff | PR #38 | `test_handoff.py` |
| WS-4 Verdict + acceptance integrity | PRs #41, #42 | `test_verdict_combination.py`, `test_acceptance_gate.py` |
| WS-5 Agent tool runtime | PR #40 | `test_tool_runtime.py` |
| WS-6 Objective-to-plan decomposition | PRs #47, #48, #49 | `test_decomposition.py`, `test_plan_approval.py`, `test_plan_runtime.py`, `test_plan_history_gate.py`, `test_persisted_task_rubrics.py` |
| WS-7 Unchoreographed loop proof | PRs #49, #50, #51 | `test_objective_to_close.py`; governed demo proof `test_demo.py` runs as a named CI step |
| Post-baseline: atomic close (issue #45) | PR #52 | `test_atomic_close.py` |
| CVE hygiene | PR #53 | Next.js pinned 15.1.12 (`frontend/package.json`) |

The issue tracker and PR queue are both **empty** (verified 2026-07-19): no
open issues, no open PRs. The product promise — *give it an objective and it
runs the loop until acceptance criteria are satisfied* — now has an
end-to-end, mock-provider, CI-enforced proof.

What "complete" does **not** yet mean is covered by the gap register below.

## 2. Gap register (verified against code, 2026-07-19)

Each gap was checked against the working tree, not inherited from prior docs.

| # | Gap | Evidence | Severity |
| --- | --- | --- | --- |
| G1 | **Dashboard is read-only.** No UI write path exists for any governed action: plan approve/reject, project start, approval-gate decisions, or halt. The only frontend POSTs are login/session and SSE plumbing (`frontend/src/app/api/session/route.ts`, `lib/api.ts`). The backend endpoints exist (`plans.py`: generate/approve/reject; `projects.py`: `/start`; `approvals` flow) — the UI simply never calls them. **CLOSED 2026-07-21** across PRs #62 (plan approve/reject, `tests/e2e/plan-approval.spec.ts`), #63 (start/halt/resume, `tests/e2e/project-controls.spec.ts`), and #66 (approval-gate decisions, project close, and objective intake; `tests/e2e/approvals.spec.ts` + the Step-1 definition-of-done proof `tests/e2e/governed-loop.spec.ts`). Every governed action is operable from the dashboard. | grep of `frontend/src` — zero calls to plan/start/approval endpoints | ~~High~~ closed |
| G2 | **No project-level halt switch.** WS-2 named "a project-level concurrency cap and a halt switch." The concurrency cap exists (`scheduler_service.py`); no halt/pause path exists anywhere in `app/` — an approved, started project cannot be stopped mid-flight through any API. **CLOSED 2026-07-19 (PR #56):** `POST /projects/{id}/halt` + `/resume` (audited, optional reason), single scheduler gate in `find_dispatchable`, audited refusals on start/dispatch; proof `tests/integration/test_halt.py`. | grep `halt`/`pause` over `backend/app` — only tool-runtime internals | ~~High~~ closed |
| G3 | **No dependency-audit CI job.** WS-8 called for `pip-audit`/`npm audit` failing on critical. CI has no such job; the Next.js CVE (#53) was caught by an external audit, not by our pipeline. **CLOSED 2026-07-21:** `dependency-audit` CI job + `scripts/dependency_audit.py` with expiring waivers; proof `backend/tests/unit/test_dependency_audit.py` and the gate itself, which caught two live criticals (`next`, `vitest`) on arrival — both fixed in the same change. | `.github/workflows/ci.yml` — no audit step | ~~Medium~~ closed |
| G4 | ~~**Live-provider path is unproven.**~~ **CLOSED 2026-07-26:** the manual `Live Provider Celery Proof` workflow ran one real GitHub Models task through HTTP dispatch → Redis → a separately started Celery worker → live provider → Postgres at merged `main` SHA `312bf334`. Run [#30207256748](https://github.com/AgentiCubed/A3/actions/runs/30207256748) passed and uploaded the sanitized, 30-day proof artifact `live-provider-proof-312bf3348dee63e3d1931d2c50375d545dc49ceb` (artifact ID `8633430992`, SHA-256 `6ddfcffde0076908a72dbdf3ed43756bfcefaf909fdc177f4c98401ab4312695`). Hermetic CI remains mock-only. | `.github/workflows/live-provider-proof.yml`; `backend/tests/integration/test_live_provider_celery_smoke.py`; run #30207256748 | ~~Medium~~ closed |
| G5 | **Optimistic-locking review under scheduler concurrency** (WS-8 item) has no recorded outcome: no ADR, no version-column usage on task transitions, no concurrency test beyond `test_atomic_close.py` (which covers closure only). | grep `version`/locking over models + state machine | Medium |
| G6 | **No deployment story past Docker Compose.** Explicitly deferred by the remediation plan "until WS-1..6 land" — they have now landed, so this is unblocked, not incomplete. | `infra/`, compose only | Low-Medium (sequenced) |
| G7 | **Doc drift.** `REMEDIATION-2026-07.md` still marks WS-6 "READY TO START"; `README.md` cites closed issue #45 as active work; `HANDOFF-WS6.md` describes as future what is now merged. Under §7 this drift is itself a defect. | this branch fixes the first two | Low (fixed here) |
| G8 | **Agentic³ platform vision: design ratified, zero implementation.** The Unified Architecture Spec v2 (#25), ontology (#18/#22), Runtime Domain spec (#23), and Implementation Blueprint (#24) are merged, but no runtime code exists (`RuntimeEventV1` appears nowhere in `backend/app`). Blueprint Phases 0–6 are all unstarted. | grep `RuntimeEvent` — no hits | Strategic (not a defect — sequenced design-first on purpose) |
| G9 | `verbal-kombat/` is an unrelated standalone artifact living in the product repo. | tree | Housekeeping |

## 3. Recommended next steps, in order

The ordering principle is the same one the remediation plan used: finish the
current product's operability before extending its ambition. A governed
autonomous loop that a human cannot start, supervise, or stop from the
product's own UI is not a completed product, whatever the backend proves.

### Step 1 — Operator control surface (closes G1 + G2) · *the completion-defining work*

Make the dashboard the place where the governed loop is actually operated:

1. **Backend first, small PR:** add the missing halt switch — a
   `POST /projects/{id}/halt` (and resume) that stops the scheduler from
   dispatching further work for the project, audited, with a state-machine-legal
   story for in-flight tasks. Done when an integration test proves a halted
   project dispatches nothing new while in-flight work concludes cleanly.
   **Done (2026-07-19, PR #56):** proof `tests/integration/test_halt.py` —
   halted projects refuse start and manual dispatch, the scheduler's
   chain-advance pass selects nothing, in-flight work concludes, and
   resume + start continues the chain.
2. **UI write paths, one focused PR per flow, in this order:**
   a. objective in → generated plan rendered → **approve / reject** buttons
      (`POST /plans`, `/plans/{id}/approve|reject`);
   b. **start** and **halt** controls on the project dashboard;
   c. pending **approval-gate decisions** (approve/reject with justification)
      surfaced from the existing approvals API.
   Done when a Playwright e2e drives objective → plan → approve → start →
   (mock) completion → close entirely through the browser, and that test runs
   in the existing e2e CI job.
   **Done (2026-07-21):** flow (a) PR #62; flow (b) PR #63; flow (c) plus the
   close control and objective intake PR #66. The definition-of-done spec is
   `tests/e2e/governed-loop.spec.ts` (objective → plan → approve → start →
   completion → close, entirely in the browser), running in the CI e2e job;
   `tests/e2e/approvals.spec.ts` proves both gate outcomes — approve
   completes the escalated task, reject returns it to READY with the
   justification recorded.

This step turns the CI-proven loop into a product a human can use.

### Step 2 — Supply-chain gate in CI (closes G3) · *small, immediate*

Add a CI job running `pip-audit` (backend) and `npm audit --audit-level=critical`
(frontend), failing on critical findings, with a documented waiver mechanism
(an allowlist file with expiry dates, so waivers cannot rot silently). Done
when the job is green on `main` and demonstrably fails on a seeded known-bad
pin in a scratch branch.

**Done (2026-07-21):** `dependency-audit` CI job + `scripts/dependency_audit.py`
+ expiring waivers in `scripts/dependency-audit-waivers.json`; decision logic
proven hermetically by `backend/tests/unit/test_dependency_audit.py`. The
failure mode was demonstrated on real data, not a seed: on arrival the gate
caught two live critical advisories on `main` — `next@15.1.12`
(GHSA-f82v-jwr5-mffw, middleware authorization bypass) and `vitest`
(GHSA-5xrq-8626-4rwp) — fixed in the same change by bumping to
`next@15.5.20` and `vitest@4.1.10`. One waiver is active: `ecdsa`
(PYSEC-2026-1325, no fix released, EC path unused — JWTs are HS256), expiring
2026-10-31.

### Step 3 — Live-provider opt-in smoke (closes G4)

A manually-triggered (`workflow_dispatch`) or nightly CI job, gated on the
presence of an `ANTHROPIC_API_KEY` secret, that runs **one** real task through
`AnthropicProvider` — dispatch → execution → evaluation — and asserts shape,
not content (hermetic CI stays mock-only per A15). Done when the job passes
against the live API and is skipped, not failed, when the secret is absent.
This is the first evidence the product works with real inference, and it
de-risks every future "use it for real" conversation.

**Done (2026-07-26):** PR [#70](https://github.com/AgentiCubed/A3/pull/70)
switched the manual workflow to the encrypted, Models-read-only
`A3_MODELS_TOKEN`. Exact-merged-SHA run
[#30207256748](https://github.com/AgentiCubed/A3/actions/runs/30207256748)
passed the opt-in test and uploaded the sanitized proof receipt. The test
proves the HTTP request queues before any worker exists, a separate worker
consumes Redis, the provider execution completes in Postgres with a provider
request receipt, the returned marker is present, evaluation passes, and the
task completes. The secret is not available to normal hermetic CI.

### Step 4 — Concurrency-safety review (closes G5)

Bounded piece of work: review task-transition writes under WS-2 concurrent
dispatch, decide optimistic locking (version column) vs. row-level locking vs.
"current serialization is sufficient," and record the outcome as an ADR either
way. If a change is needed, it comes with a concurrency test in the spirit of
`test_atomic_close.py`. Done when the ADR exists and cites its test.

### Step 5 — Minimal deployment story (closes G6)

Now unblocked. Smallest honest increment: a production compose profile or a
single-node container deployment guide (managed Postgres/Redis, TLS
termination, secret injection, backup/restore of the audit-bearing database),
plus a smoke script. Kubernetes/Temporal remain out of scope until demand
exists (ADR-0002 already reserves the port).

### Step 6 — Agentic³ Phase 0, then the Phase 1 vertical slice (G8)

Only after Steps 1–3: begin the blueprint's own sequence —

- **Phase 0** (documentation-only): reconcile v2/ontology/Runtime contracts,
  record the authority matrix and reversible-work standing policy under
  `docs/governance/decisions/`, per blueprint §10.
- **Phase 1**: the `RuntimeEventV1` event-ledger vertical slice, disabled by
  default behind a flag, per blueprint acceptance criteria.

The blueprint is explicit that Phase 1 is deliberately small; resist starting
it while the operator control surface (Step 1) is unfinished, or the platform
will again outrun the product.

### Housekeeping (G7, G9)

- G7 is fixed in this branch: `REMEDIATION-2026-07.md` statuses updated with
  citations; README's stale issue-#45 reference corrected.
- G9: move `verbal-kombat/` to its own repository (it is self-contained —
  one HTML file) or explicitly record why it lives here. No urgency.

## 4. Sequencing rationale

```
Step 1 (operate the loop from the UI)  ──►  product is COMPLETE as claimed
Step 2 (CI supply-chain gate)          ──►  cheap, do immediately, in parallel
Step 3 (live-provider smoke)           ──►  first real-inference evidence
Step 4 (concurrency ADR)               ──►  bounded risk retirement
Step 5 (deploy story)                  ──►  unblocked, demand-driven
Step 6 (Agentic³ Phase 0/1)            ──►  only after 1–3; design already ratified
```

Steps 1–2 together are the honest definition of "completed product v1": the
CI-proven governed loop, operable end-to-end by a human from the product's own
UI, with the supply chain guarded. Steps 3–5 harden it. Step 6 begins the next
product.

## 5. Standing conventions that bind this plan

Unchanged from `REMEDIATION-2026-07.md` §7 and `HANDOFF-WS6.md` §5: focused
draft PRs off `main`, one workstream per PR; claims cite CI tests or are
marked *(planned)*; progress credit only for merged default-branch work;
hermetic CI never calls a live provider (the Step-3 job is opt-in and
secret-gated precisely to preserve this).
