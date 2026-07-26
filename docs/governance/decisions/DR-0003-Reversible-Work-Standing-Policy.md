# DR-0003 — Reversible Work Standing Policy

## Registration block

Machine-verifiable header required by the Implementation Blueprint (Phase 2:
the dispatcher verifies this artifact's stable ID, version, digest, scope,
and expiry through a read-only policy adapter before issuing any lease).

- **Stable ID:** DR-0003
- **Version:** 1.0.0-draft
- **Ratification status:** **Proposed — awaiting explicit ratification by the
  Principal.** Per DR-0001: agreement among Executors, Evaluators, advisers,
  reviewers, or automated systems does not constitute ratification. **This
  policy confers no authority while Proposed.**
- **Digest:** computed over this file's bytes at ratification and recorded in
  the ratification record (RR series); recomputed and re-recorded on every
  ratified version change. A dispatcher must reject a registration whose
  digest does not match the ratified record.
- **Scope:** the Agentic³ Runtime Domain (RT-101–RT-110) operating within
  this repository's governance; one work class (§Decision 3)
- **Expiry:** 180 days from ratification date, or upon supersession or
  revocation, whichever is first. Expiry removes standing authority; it does
  not stop observation and recording.

## Purpose

Phase 0 of the Implementation Blueprint requires "a Principal-ratified
reversible-work standing policy as a versioned governance decision under
`docs/governance/decisions/`." This Decision Record is that policy: it fixes
the classification of actions into reversible and irreversible, and grants
the Runtime Domain standing authority for exactly one narrow class of
reversible work — so that later phases can dispatch that class without a
fresh per-item human approval, while everything else remains undispatchable
without explicit current authority.

## Context

The Runtime Domain Specification v1.0 (adopted) and the Implementation
Blueprint both forbid the Runtime to authorize its own work: a Work Item is
a proposal, not authorization, and dispatch requires either an explicit
authorization artifact or a pre-approved reversible standing policy. No such
standing policy exists yet, which leaves Phase 2 unbuildable and Phase 1
scoped to observation only. The two sources also state the
reversible/irreversible boundary with small divergences; the Phase 0
Reconciliation Record (`docs/agentic3/PHASE0-RECONCILIATION.md` §4) resolves
those by union — this policy records the reconciled classification as the
governed artifact.

## Decision

1. **Action classification.** Every action the Runtime can initiate,
   schedule, or dispatch is classified as follows:

   - **Irreversible (enumerated):** merge; protected-branch push; tag
     creation, deletion, or movement; release publication; history rewrite;
     branch deletion; branch-protection or ruleset changes; secret rotation
     or secret handling of any kind; destructive cleanup; deletion or
     mutation of any append-only record; external communication on behalf of
     the Principal; payment or procurement.
   - **Classification default (fail closed):** an action not explicitly
     classified is treated as **irreversible** until a ratified revision of
     this policy classifies it. "Unknown destructive actions" are
     quarantined, never dispatched.
   - **Reversible:** an action is classifiable as reversible only if it can
     be fully undone from within the system by a subsequent action requiring
     no external party, no history rewrite, and no loss of recorded state.

2. **Non-authorizers.** Schedule, timeout, urgency, silence, inferred
   intent, and model confidence never authorize any action (reconciled
   union of RT-SPEC §5 and Blueprint §1). Retry of an irreversible action
   always requires fresh **human** authorization.

3. **The standing-authorized work class (exactly one).** While this policy
   is ratified, unexpired, and unrevoked, the Runtime holds standing
   authority to dispatch only:

   > **WC-OBS-1 — Observation and recording:** ingesting approved source
   > events, normalizing them to `RuntimeEventV1`, appending them to the
   > append-only `runtime_events` ledger, writing ingest receipts, outbox
   > records, quarantine records, checkpoints, telemetry, and notifications.

   Properties that make WC-OBS-1 reversible in the sense of Decision 1:
   ingestion can be disabled by one flag; ledger rows are append-only
   additions whose effect on any downstream consumer is nil while later
   phases remain unbuilt; no external side effect exists.

4. **Explicit non-grants.** This policy does not grant authority to:
   dispatch any Work Item beyond WC-OBS-1; take any enumerated irreversible
   action; create, broaden, or extend this policy or any delegation
   (Runtime cannot mint its own authority — Blueprint §8.1); act outside
   the registered scope or after expiry/revocation; or treat `ready`
   Assurance findings, verification passes, or accumulated evidence as
   authorization.

5. **Verification at dispatch.** Before honoring this policy, a dispatcher
   must verify — through a read-only policy adapter — that the registered
   stable ID, version, digest, scope, and expiry match the ratified record,
   and that no revocation is recorded. A mismatch or unavailability of the
   record means no standing authority exists (fail closed; observation and
   recording under an already-issued lease may complete, nothing new is
   dispatched).

6. **Revocation and amendment.** The Principal may revoke this policy at
   any time by recording a revocation in the ratification record; revocation
   is effective immediately upon recording. Amendment follows the same path
   as ratification (new version, new digest, new record). Nothing in this
   policy may be amended by the Runtime, an Executor, or an Evaluator.

## Consequences

### Positive

- Phase 1 can ship its event-ledger slice with a lawful basis for the only
  thing it does (observe and record), and Phase 2's dispatcher has a
  concrete artifact to verify.
- The irreversible enumeration and the fail-closed default give every future
  work-class discussion a fixed starting point: new authority requires a
  ratified revision, never an inference.

### Costs

- A 180-day expiry means the Principal must re-ratify periodically or
  standing work stops — deliberate: unattended authority should decay.
- The fail-closed default will occasionally classify genuinely harmless
  actions as irreversible until a revision lands. That friction is the
  control working.

## Authority and scope

This Decision Record is subordinate to the AgentiCubed Constitution and to
DR-0001's ratification requirements. It takes effect only upon explicit
ratification by the Principal; a ratification record in the RR series shall
record the ratified version and digest. Where this document conflicts with
the Constitution, the Constitution controls.
