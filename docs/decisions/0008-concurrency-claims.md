# ADR-0008: Concurrency safety via conditional-UPDATE state claims

- **Status:** Accepted
- **Date:** 2026-07-26
- **Resolves:** `docs/NEXT-STEPS-2026-07.md` Step 4 (gap G5)
- **Related:** ADR-0007 (stabilization), the acceptance boundary introduced
  with the WS-4b atomic-close work

## Context

WS-2 made concurrent dispatch a normal operating condition: the scheduler, the
worker, and direct API dispatch can all try to move the same task at the same
time, and an operator can decide a gate while the loop is still running. The
roadmap asked for a bounded review of task-transition writes under that
concurrency, with an explicit decision between:

1. **Optimistic locking** — a generic `version_id_col` on mutable rows, every
   ORM flush guarded by a version predicate;
2. **Row-level locking** — `SELECT ... FOR UPDATE` around read-modify-write
   sections;
3. **"Current serialization is sufficient"** — record why and stop.

### What the review found

The codebase already serializes its critical transitions with a fourth,
narrower pattern: **conditional-UPDATE state claims**. The current state is
part of the `WHERE` clause, the database's row-write arbitration picks exactly
one winner, and `rowcount` tells the losers they lost:

- **Governed dispatch/execution claim** —
  `execution_service._compare_and_transition_governed` issues
  `UPDATE tasks SET status = :to WHERE id = :id AND status = :expected`; the
  loser gets `AlreadyQueued` (an `IllegalTransition` surfaced as a 409). Every
  governed step to `QUEUED` and the first `RUNNING` claim goes through it, and
  the claim is committed *before* any provider call can produce an external
  side effect.
- **Acceptance boundary** — `acceptance_boundary_service.claim_acceptance_write`
  / `lock_acceptance_for_close` update the project row conditionally on
  `status != CLOSED`. On PostgreSQL this doubles as a per-project row lock
  (competing UPDATEs wait, then re-check the predicate); `acceptance_revision`
  is additionally an optimistic guard the close path re-checks before its
  final commit, so a stale acceptance snapshot cannot authorize a close.
- **Double-enqueue guard** — `execution_service.queue_task` rejects a task
  that is already `QUEUED`, so a re-dispatch cannot enqueue a second worker
  message for the same task.

The review found **one** critical write outside the pattern:
`approval_service.decide_approval` checked `status == PENDING` on an
already-loaded ORM instance and then assigned — a read-then-write. Two
concurrent deciders (two operators, or a double-submit) could both pass the
check: both would record a decision on one gate, and the linked task's
transition could run twice, with the final task state depending on commit
order. On a governance record whose entire purpose is an exactly-once human
decision, that is a real gap, however narrow the window.

Non-critical remainder: tasks *without* plan provenance
(`source_plan_id IS NULL`) still transition through plain ORM assignments
(`_move_to_queued` / `_transition`). These are the legacy single-dispatch
paths; the governed loop — the product — always carries provenance, the
scheduler only dispatches governed tasks, and the legacy path is exercised by
one operator invoking one dispatch call. Two deliberately concurrent dispatch
calls against a legacy task could double-run it, costing a duplicate provider
call; no governance record is corrupted because the acceptance boundary and
the double-enqueue guard still apply.

## Decision

**Keep and extend the conditional-UPDATE claim pattern; adopt neither a
generic version column nor broad row-level locking.**

1. Conditional-UPDATE claims at state choke points remain the canonical
   serialization mechanism for this codebase. The state machine's own
   persisted state is the version: a claim names the state it expects and the
   database arbitrates. This is optimistic locking specialized to exactly the
   rows and transitions that need it, with a governed 409 for the loser
   instead of a retry loop.
2. A generic `version_id_col` is rejected: it would guard every flush of every
   mutable row, turn benign concurrent metadata edits into user-facing
   conflicts, and still would not express *which* transition was claimed —
   the audit trail wants "QUEUED → RUNNING was won once," not "row version
   advanced."
3. Broad `SELECT ... FOR UPDATE` is rejected as the general mechanism: it
   serializes readers that don't need it, and SQLite (the hermetic test
   database) ignores it, so tests could not prove the behavior CI relies on.
   The one place a row lock is genuinely wanted — the acceptance boundary —
   already gets it implicitly from the conditional UPDATE on PostgreSQL.
4. `decide_approval` is brought into the pattern (in this change): the
   decision is a conditional UPDATE on `status = PENDING`; the loser receives
   `AlreadyDecided` (409), and only the winner advances the linked task.
5. The legacy ungoverned-task path is **accepted as-is** and recorded here:
   its worst case is a duplicated provider call on a manually double-dispatched
   task, it cannot corrupt governance records, and it is expected to shrink as
   governed plans become the only dispatch surface. Extending the claim
   pattern there is welcome if the path ever becomes concurrent by design.

## Consequences

- Any new state-machine write that can race (scheduler vs. worker vs. API vs.
  operator) must use a conditional-UPDATE claim with the expected state in the
  predicate, surface the lost race as a governed 409, and synchronize the
  in-memory instance via `set_committed_value` so a later flush cannot emit a
  stale unconditional write.
- Deciders can now receive `409 already_decided` where they previously might
  have silently double-written; the UI already renders that refusal
  (`ApprovalsPanel` shows decided-gate 409s).

## Tests

The decision cites, and is enforced by, the following tests:

- `backend/tests/unit/test_approval_decision_claim.py::test_concurrent_deciders_record_exactly_one_decision`
  — added with this ADR: an approver and a rejecter race one gate; exactly one
  decision and one audit record survive, the loser gets `AlreadyDecided`.
- `backend/tests/unit/test_governed_dispatch_claim.py` — duplicate workers get
  exactly one `RUNNING` claim; concurrent queue requests submit exactly one
  governed claim.
- `backend/tests/integration/test_objective_to_close.py::test_governed_dispatch_claim_allows_one_queue_and_one_execution`
  — the claim holds through the full API surface.
- `backend/tests/integration/test_atomic_close.py` (seven tests) — close
  serializes with concurrent evidence writes; a stale acceptance snapshot
  cannot commit a close; late evidence after close is rejected.
