# ADR-0008: Concurrency safety of task dispatch transitions

- **Status:** Accepted
- **Date:** 2026-07-26
- **Resolves:** gap G5 in `docs/NEXT-STEPS-2026-07.md` (the WS-8
  "optimistic-locking review on task transitions" item, previously without a
  recorded outcome)
- **Related:** issue #45 / PR #52 (atomic project close), WS-6 governed
  dispatch claims

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
3. **Transitions that remain read-then-write are accepted, with reasons:**
   - *Mid-attempt retry transitions* inside `execute_task`
     (FAILED→RUNNING within the retry loop): the executing session owns the
     task for the whole attempt loop; a competing dispatcher is fenced out
     by the RUNNING claim it cannot win.
   - *Approval decisions and other human-paced transitions*
     (`transition_task`): serialized per project by the
     `claim_acceptance_write` row-claim, and the approval row itself
     rejects a second decision (`AlreadyDecided`).
   - *Reassignment to READY* (`reassign_task`): human-paced, and any
     subsequent dispatch must still win the QUEUED claim.

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
