# Agentic³ Authority Matrix

- **Status:** Phase 0 record (IMPLEMENTATION-BLUEPRINT §10 Phase 0 "record
  … authority matrix")
- **Date:** 2026-07-27
- **Sources:** [`IMPLEMENTATION-BLUEPRINT.md`](./IMPLEMENTATION-BLUEPRINT.md)
  §3/§8 ("BP") and the
  [Runtime Domain Specification v1.0](../governance/runtime/Runtime-Domain-Specification-v1.0.md)
  §1–§2 ("RT-SPEC"), reconciled per
  [`PHASE0-RECONCILIATION.md`](./PHASE0-RECONCILIATION.md) §4
- **Authority:** This matrix *records* the adopted boundaries; it confers
  none. Authority is granted only through explicit governance relationships
  (Constitution; DR-0001). Where this record and a ratified decision ever
  diverge, the ratified decision governs and this record must be corrected
  by an appended revision.

---

## 1. Reading rules

1. **"May not" lists are closed-world for authority:** anything not in an
   engine's "may" column is outside its authority — fail closed.
2. Governance is implemented as a peer engine **inside the Executive
   Domain** (reconciliation R-1). The authority boundary is
   placement-invariant: if a separate Governance Domain is later
   established, only package composition changes, never this matrix.
3. The **six non-authorizers** (R-8, union): schedule, timeout, silence,
   inferred intent, urgency, and model confidence can never cause
   irreversible promotion or substitute for an authorization artifact.
4. An **executor cannot transition its own work** to `VERIFIED_PASS`,
   `READY_FOR_PROMOTION`, or `PROMOTED` (R-7 — all three states, with no
   "directly" qualifier), and cannot be the sole evaluator of its own
   material action.
5. The adopted decision boundary (DR-0004 P-5): *Verification evaluates
   evidence; Assurance evaluates readiness and unresolved risk; Governance
   supplies authority.* None substitutes for another.

## 2. Engine authority matrix

| Engine (domain) | May | May not |
|---|---|---|
| Intent (Executive) | Record and preserve Principal objectives, constraints, acceptance criteria with provenance | Authorize work; redefine the Principal's intent |
| Planning (Executive) | Decompose approved intent into plans, milestones, tasks, dependencies, risks | Redefine success; approve its own plan |
| Orchestration (Executive) | Assign and coordinate bounded, authorized execution | Authorize irreversible action; certify completion |
| Governance (Executive) | Grant bounded authority the Principal/policy actually holds: delegations, boundaries, gates, permissions, `allow/deny/halt/escalate` decisions | Execute work; fabricate evidence; grant authority it does not hold |
| Verification (Intelligence) | Evaluate fixed, pre-execution criteria against evidence; record `pass/fail/unknown` | Authorize action; verify its own execution; change criteria after execution |
| Memory (Intelligence) | Capture, classify, checkpoint; append FR/RM/IER/RL/TET records with provenance | Determine truth; promote knowledge; confer authority |
| Knowledge (Intelligence) | Answer semantic/contradiction queries; **propose** gravity changes and Genome membership | Ratify, authorize, or automatically promote/demote anything |
| Evolution (Intelligence) | Propose experiments, candidates, reopenings as reversible review work | Amend, deploy, or promote its own proposal |
| Assurance (Assurance) | Decide readiness over evidence, risk, verification, and governance constraints (`ready/not_ready/more_evidence_required`) | Execute; mutate evidence; grant authority; replace human acceptance (`ready` is not authorization) |

## 3. Runtime component authority (RT-101…RT-110)

The Runtime Domain manages work; it holds no product, constitutional, or
release authority and cannot certify its own success. It may initiate and
coordinate **reversible** workflows only; irreversible action requires an
explicit Governance authorization artifact and, where required, an
Assurance decision.

| ID | Component | May | May not / constraints |
|---|---|---|---|
| RT-101 | Event Observer | Read approved sources; emit **raw** observations with source identity, timestamps, adapter version, digest | Treat observation as authority; produce canonical events (that is RT-102's role, R-4) |
| RT-102 | Event Normalizer | Validate/normalize raw events into `RuntimeEventV1`; create quarantine records | Invent missing facts; coerce ambiguous input (quarantine instead); normalize a missing required actor to null (R-3) |
| RT-103 | Scheduler | Turn approved temporal policies and review triggers into **proposed** work; report missed schedules | Initiate anything beyond pre-authorized reversible work classes; a schedule never grants irreversible authority |
| RT-104 | Queue Manager | Prioritize within the approved queue policy; manage dependencies, aging, blocked/quarantined states | Broaden scope; convert a proposal into authorization; let urgency override constitutional boundaries; invent priority weights (R-14) |
| RT-105 | Dispatcher | Validate authority and capability; issue expiring `ExecutionLeaseV1` and exact executor packet | Dispatch beyond explicit scope/capability; inherit authority from later gates; proceed on repository/identity mismatch (STOP); issue a lease without verifying the registered standing-policy ID, version, digest, scope, and expiry |
| RT-106 | Execution Monitor | Track heartbeats, deadlines, stop conditions; halt, expire, or retry **reversible** work under policy; propose escalation | Hide failure; approve completion; treat missing heartbeat as anything but unknown-until-timeout; retry an irreversible action without fresh **human** authorization (R-12) |
| RT-107 | Synchronizer | Append reconciliation, conflict, and contradiction records against explicit source precedence | Silently overwrite authoritative history; resolve contradictions by deletion (see [`PRECEDENCE-AND-RETENTION.md`](./PRECEDENCE-AND-RETENTION.md)) |
| RT-108 | Checkpoint Manager | Capture immutable, context-complete checkpoints distinguishing facts, inference, decisions, unknowns, pending authority (R-5) | Certify the recorded state; mutate an existing checkpoint |
| RT-109 | Telemetry and Health | Derive metrics and health status from transitions; observe and report only | Present metrics as truth; report `HEALTHY` from process uptime alone; include sensitive payloads |
| RT-110 | Notifier / Escalation Router | Deliver deduplicated decision requests, alerts, digests; explain urgency | Treat silence as approval; expand sensitive detail |

## 4. Cross-cutting prohibitions (all engines, all components, all agents)

1. **Irreversible actions require a current, exact human authorization
   artifact:** merge, protected-branch push, tag creation/mutation/movement,
   release publication, history rewrite, branch deletion, protection or
   ruleset changes, secret rotation, and destructive cleanup. The
   side-effect adapter is the final hard control: it rejects an irreversible
   call without the exact, unexpired, unrevoked human authorization and any
   required Assurance decision — Runtime cannot mint either artifact.
2. **Degraded mode fails closed (R-13):** if Governance, Verification,
   Assurance, Memory, or Knowledge is unavailable, only pre-authorized
   reversible observation and recording continue; **dispatch**, promotion,
   and irreversible action stop.
3. **Agent identities cannot self-govern (BP §8.3):** no agent identity may
   grant permissions, expand its scope, disable controls, issue Governance
   or Assurance decisions, or alter its own delegation.
4. **Distinct record kinds stay distinct (BP §1 invariant 5):** facts,
   reports, proposals, decisions, authorizations, verification, and
   assurance outcomes are never conflated; a command is never evidence its
   outcome occurred.
5. **The sole standing work class is WC-OBS-1**
   ([DR-0003 v1.0.0, ratified](../governance/decisions/DR-0003-Reversible-Work-Standing-Policy.md)):
   observation and recording. Everything else awaits case-by-case
   authorization or a future ratified policy version.
6. **Component contracts are structured in the manner AC-0003 *proposes***
   (Mission, Inputs, Outputs, Dependencies, Authority, Constraints,
   Evidence, Learning) — AC-0003 is a candidate, not adopted, and this
   structure does not promote it (R-15).

## 5. Maintenance

Changes to any boundary in this matrix require the same authority as the
source they record: a reconciliation ruling for wording, a ratified decision
for substance. Revisions are appended with date, basis, and link — prior
rows are never silently rewritten.
