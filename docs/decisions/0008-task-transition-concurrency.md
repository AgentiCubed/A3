# ADR-0008: Concurrency safety of task dispatch transitions

- **Status:** Accepted
- **Date:** 2026-07-26
- **Resolves:** gap G5 in `docs/NEXT-STEPS-2026-07.md` (the WS-8
  "optimistic-locking review on task transitions" item, previously without a
  recorded outcome)
- **Related:** issue #45 / PR #52 (atomic project close), WS-6 governed
  dispatch claims
- **Consolidates:** two independently merged records of the same Step-4
  review (PR #69: dispatch transitions; PR #71: approval decisions, formerly
  `0008-concurrency-claims.md`). Both reached the same decision — the
  conditional-UPDATE claim pattern — and this file is now the single ADR-0008.

## Context

The July 2026 remediation left one concurrency question without a recorded
answer: are task state transitions safe under concurrent dispatch — two
scheduler passes, a manual dispatch racing the scheduler, or a redelivered
worker message racing a live worker?

The line-verified state before this decision:

- **Governed (plan-derived) tasks** already claimed their dispatch
  transitions atomically: a conditional
  `UPDATE tasks SET status=:to WHERE id=:id AND status=:expected` makes the
  persisted row the arbiter; exactly one caller wins and the loser raises
  `AlreadyQueued` (`execution_service._compare_and_transition`, proven by
  `tests/unit/test_governed_dispatch_claim.py`).
- **Project closure** is serialized with every acceptance-evidence writer
  through the `acceptance_revision` row-claim
  (`acceptance_boundary_service`), proven by
  `tests/integration/test_atomic_close.py`.
- **Legacy (non-plan) tasks**, however, still used ORM read-then-write
  transitions for the same dispatch steps: two sessions that both read
  READY (or QUEUED) before either committed could both queue — or both
  start — the same task. The in-memory `AlreadyQueued` pre-check only
  catches the race after the winner's commit is visible.
- The hermetic test suite runs on SQLite, which ignores
  `SELECT ... FOR UPDATE` — so any guarantee relying on row locks is
  unprovable in CI's main suite. Conditional-UPDATE claims, by contrast,
  are honored identically on SQLite and PostgreSQL.

## Decision

1. **The conditional-claim (compare-and-swap) pattern is the arbiter for
   every dispatch-critical task transition, for all tasks.** The governed
   helpers were generalized (`_compare_and_transition`, `_claim_queued`,
   `_claim_execution`) and the legacy read-then-write path
   (`_move_to_queued` + unconditional RUNNING transition) was deleted.
   `queue_task` and `execute_task` now route every task through the claims.
   A lost claim raises `AlreadyQueued` (an `IllegalTransition`), which the
   API maps to HTTP 409 and the scheduler already catches.
2. **New concurrency guarantees are expressed as conditional UPDATEs, not
   row locks**, so the hermetic suite can prove them (see Context on
   SQLite).
3. **Approval decisions are exactly-once via the same claim pattern.**
   `approval_service.decide_approval` was a read-then-write on
   `approval.status`: two concurrent deciders (two operators, or a
   double-submit) could both pass the PENDING check, both record a decision
   on one gate, and double-advance the linked task. The decision is now a
   conditional `UPDATE ... WHERE status = PENDING`; the loser receives
   `AlreadyDecided` (the 409 the UI already renders) and only the claim
   winner advances the task. Proven by
   `tests/unit/test_approval_decision_claim.py`.
4. **Transitions that remain read-then-write are accepted, with reasons:**
   - *Mid-attempt retry transitions* inside `execute_task`
     (FAILED→RUNNING within the retry loop): the executing session owns the
     task for the whole attempt loop; a competing dispatcher is fenced out
     by the RUNNING claim it cannot win.
   - *Post-decision task advancement and other human-paced transitions*
     (`transition_task`): the approval-decision claim admits exactly one
     decider, so the advancement runs at most once; project closure is
     fenced by the `claim_acceptance_write` row-claim.
   - *Reassignment to READY* (`reassign_task`): human-paced, and any
     subsequent dispatch must still win the QUEUED claim.
5. **A generic ORM version column and broad `SELECT ... FOR UPDATE` are
   both rejected** as the general mechanism. The state machine's own
   persisted state is the version: a claim names the state it expects and
   the database arbitrates. A `version_id_col` would guard every flush of
   every mutable row, turn benign concurrent metadata edits into
   user-facing conflicts, and still not express *which* transition was
   claimed. Broad row locks serialize readers that don't need it — and
   SQLite ignores them (see Context), so CI could not prove them.

## Consequences

- A raced legacy dispatch now loses loudly (409) instead of silently
  double-executing — including the broker-redelivery case where two workers
  hold the same QUEUED task and only one can claim RUNNING before provider
  work begins.
- Proof: `tests/integration/test_transition_concurrency.py` — two real
  database sessions race the QUEUED claim and the RUNNING claim on a legacy
  task; exactly one wins, the audit trail records a single transition walk,
  and both tests fail against the pre-decision code.
- Audit shape for legacy dispatch transitions is now identical to governed
  ones (same `task.transition` before/after records, emitted by the claim).
- No schema change and no version column: optimistic locking via a version
  column (the alternative considered) was rejected as strictly heavier —
  it requires a migration and retry semantics at every writer while
  providing the same arbiter the status predicate already provides.
- Any new state-machine write that can race (scheduler vs. worker vs. API
  vs. operator) must use a conditional-UPDATE claim with the expected state
  in the predicate, surface the lost race as a governed 409, and synchronize
  the in-memory instance via `set_committed_value` so a later flush cannot
  emit a stale unconditional write.
- Deciders can receive `409 already_decided` where they previously might
  have silently double-written; the UI already renders that refusal.
