# Runtime Domain Specification v1.0

- **Status:** Proposed architecture baseline
- **Issue:** [AgentiCubed/agenticubed#17](https://github.com/AgentiCubed/agenticubed/issues/17)
- **Authority:** Subordinate to the Constitution, Foundational Concepts, TARP-0001,
  the Upward Compatibility Rule, and the Agentic³ ontology

## Purpose and foundational rule

The Runtime Domain is the continuously operating coordination layer of Agentic³.
It observes events, schedules governed work, manages queues, synchronizes state,
records checkpoints, emits telemetry, and notifies authorized Principals without
depending on an active chat session.

The Runtime Domain manages work. It does not possess product, constitutional, or
release authority and cannot certify its own success.

> The Runtime Domain may initiate and coordinate reversible workflows, but it
> may not authorize or perform irreversible actions without an explicit
> authorization artifact from the Governance Domain and, where required, an
> `AssuranceDecision`.

Irreversible actions include merge, protected-branch push, tag creation,
deletion, or movement, release publication, history rewrite, branch deletion,
protection or ruleset changes, secret rotation, and destructive cleanup.

## 1. Boundary

### In scope

- Receive internal and external events and normalize them into canonical
  envelopes.
- Evaluate approved routing and scheduling rules.
- Create, prioritize, queue, and dispatch bounded work.
- Track leases, retries, deadlines, dependencies, and stop conditions.
- Synchronize authoritative state into project and institutional memory.
- Emit telemetry, alerts, digests, and checkpoints.
- Halt or quarantine work when authority, evidence, identity, schema validity,
  or state is insufficient.
- Preserve audit evidence for every state transition.

### Out of scope

- Redefining human intent or changing constitutional or foundational authority.
- Approving its own output or bypassing Governance, Verification, or Assurance.
- Storing or exposing secrets or silently mutating source-of-truth records.
- Treating conversational memory as repository truth.
- Autonomous merge, tag, release, protection change, destructive cleanup, or
  secret rotation.

## 2. Component contracts

Each component follows AC-0003 Architectural Contracts: Mission, Inputs, Outputs,
Dependencies, Authority, Constraints, Evidence, and Learning.

### RT-101 — Event Observer

- **Mission:** Detect relevant changes from approved sources without treating
  observation as authority.
- **Inputs/outputs:** GitHub, CI, repository, schedule, internal-engine, and
  operator events become canonical `RuntimeEvent` envelopes.
- **Dependencies:** Source adapters, identity registry, clock, and ontology.
- **Authority:** Read approved sources and emit observations.
- **Constraints:** Preserve source identity and delivery metadata; tolerate
  duplicate delivery.
- **Evidence/learning:** Source URI and ID, source and receipt times, payload
  digest, adapter version, missed/noisy events, and duplication rates.

### RT-102 — Event Normalizer

- **Mission:** Convert heterogeneous events into a stable model.
- **Inputs/outputs:** Raw events become validated `RuntimeEvent` objects or
  quarantine records.
- **Dependencies:** Ontology, schema registry, and identity resolver.
- **Authority:** Normalize and classify, never invent missing facts.
- **Constraints:** Preserve safe unknown fields; quarantine invalid or ambiguous
  input rather than coercing it.
- **Evidence/learning:** Schema version, normalization log, validation result,
  original digest, schema drift, and recurring ambiguity.

### RT-103 — Scheduler

- **Mission:** Create due work from approved schedules and temporal policies.
- **Inputs/outputs:** Schedules, calendars, deadlines, and review triggers
  produce proposed `WorkItem` objects.
- **Dependencies:** Clock, Governance policy, and Queue Manager.
- **Authority:** Initiate only reversible, pre-authorized work classes.
- **Constraints:** A schedule never grants irreversible authority; report missed
  schedules rather than silently skipping them.
- **Evidence/learning:** Schedule ID/version, due and creation times,
  authorization basis, cadence utility, and operational cost.

### RT-104 — Queue Manager

- **Mission:** Maintain the authoritative backlog and explainable ordering.
- **Inputs/outputs:** Events, scheduled work, operator requests, and proposals
  produce a prioritized queue, dependency graph, and blocked/quarantined states.
- **Dependencies:** Governance, Risk, Orchestration, and identity registry.
- **Authority:** Prioritize within policy, without broadening scope or converting
  a proposal into authorization.
- **Constraints:** Audit priority changes, age waiting work, and never let
  urgency override constitutional boundaries.
- **Evidence/learning:** Priority factors, policy version, dependencies, risk,
  state history, delay cost, and observed outcomes.

### RT-105 — Dispatcher

- **Mission:** Lease authorized work to an eligible executor.
- **Inputs/outputs:** Ready work and executor capability/availability produce an
  `ExecutionLease`, dispatch event, and exact executor packet.
- **Dependencies:** Orchestration Engine, Governance authorization, and
  capability registry.
- **Authority:** Dispatch only within explicit scope and capability.
- **Constraints:** Leases expire; scope cannot self-expand; authority from later
  gates is not inherited; repository or identity mismatch causes STOP.
- **Evidence/learning:** Work version, executor, duration, authorization artifact,
  task packet, capability mismatch, and executor reliability.

### RT-106 — Execution Monitor

- **Mission:** Track leases, heartbeats, evidence, deadlines, and stop conditions.
- **Inputs/outputs:** Executor/tool/CI reports and operator intervention produce
  progress, timeout, retry, halt, or escalation events.
- **Dependencies:** Dispatcher, Telemetry, and Governance.
- **Authority:** Halt, expire, or retry reversible work under policy; never hide
  failure or approve completion.
- **Constraints:** Missing heartbeat remains unknown until timeout; retries are
  bounded and recorded.
- **Evidence/learning:** Timestamps, lease state, commands, exit codes, artifacts,
  failures, timeout classes, and retry outcomes.

### RT-107 — Synchronizer

- **Mission:** Reconcile runtime state with authoritative project, repository,
  governance, and memory sources.
- **Inputs/outputs:** Source snapshots and verified outputs produce
  synchronization plans, conflict records, memory proposals, and provenance.
- **Dependencies:** Memory and Knowledge Engines, adapters, and ontology.
- **Authority:** Append verified synchronization records; never silently
  overwrite contradictory authoritative history.
- **Constraints:** Source precedence is explicit; corrections preserve prior
  state.
- **Evidence/learning:** Before/after references, authority ranking, decisions,
  digests, stale sources, and recurring divergence.

### RT-108 — Checkpoint Manager

- **Mission:** Capture context-complete state at meaningful boundaries.
- **Inputs/outputs:** Gates, milestones, decisions, incidents, and schedules
  produce immutable or append-only `RuntimeCheckpoint` artifacts.
- **Dependencies:** Memory Engine, TARP-0001, and ontology.
- **Authority:** Record supplied state, never certify it.
- **Constraints:** Distinguish verified facts, inference, decisions, unknowns,
  and pending authority.
- **Evidence/learning:** Source references, repository identifiers, active work,
  risks, contradictions, and reconstruction cost.

### RT-109 — Telemetry and Health

- **Mission:** Measure reliability, throughput, correctness signals, and
  governance compliance.
- **Inputs/outputs:** State and health events produce metrics, health status,
  service indicators, and anomalies.
- **Dependencies:** Component event streams, clock, and metric registry.
- **Authority:** Observe and report only.
- **Constraints:** Metrics are not truth; avoid sensitive payloads, vanity
  metrics, and false precision.
- **Evidence/learning:** Versioned metric definitions, source events, aggregation
  windows, bottlenecks, false alarms, and silent failures.

### RT-110 — Notifier and Escalation Router

- **Mission:** Deliver actionable information to the correct Principal or
  subsystem at the correct urgency.
- **Inputs/outputs:** Alerts, blocked work, authorization requests, digests, and
  incidents produce notifications, escalation packets, and acknowledgements.
- **Dependencies:** Role/contact registry, Governance, and preference policy.
- **Authority:** Notify and request decisions; silence is never approval.
- **Constraints:** Deduplicate noise, explain urgency, and minimize sensitive
  detail.
- **Evidence/learning:** Recipient resolution, delivery, acknowledgement,
  escalation timer, actionability, latency, and alert fatigue.

## 3. Canonical event model

```text
RuntimeEvent
- event_id: stable unique identifier
- event_type: controlled vocabulary
- schema_version
- source_system
- source_entity_id
- source_uri
- source_timestamp
- received_timestamp
- actor_id (nullable only when the event schema declares a passive observation
  or schedule tick actor-less; quarantine a missing actor for every other class)
- subject_entity_id
- project_id / repository_id (when applicable)
- correlation_id
- causation_id
- payload_digest
- payload_reference
- classification: fact | report | proposal | decision | authorization |
  verification | alert
- sensitivity
- trust_level
- idempotency_key
- ontology_relationships[]
- provenance[]
```

Event classes are `observed.*`, `proposed.*`, `authorized.*`, `dispatched.*`,
`executing.*`, `reported.*`, `verified.*`, `assured.*`, `governed.*`,
`synchronized.*`, `learned.*`, `failed.*`, and `quarantined.*`.

Events are immutable observations. A correction is a new event linked by
`corrects` or `supersedes`; the original is never erased.

## 4. Work item model

```text
WorkItem
- work_id
- version
- objective
- origin_event_id
- project/repository scope
- allowed_actions[]
- prohibited_actions[]
- allowed_files/resources[]
- expected_outputs[]
- acceptance_criteria[]
- verification_plan
- authority_required
- current_authorization_artifact
- risk_class
- priority
- dependencies[]
- deadline (optional completion bound evaluated by policy; deadline expiry
  causes a recorded escalation or `EXPIRED` transition, never silent
  cancellation)
- review_trigger (optional condition evaluated on each referenced event and
  schedule tick to open review or revalidation)
- eligible_executor_capabilities[]
- retry_policy
- stop_conditions[]
- state
- state_history[]
- evidence_refs[]
- learning_refs[]
```

A `WorkItem` is not authorization. It is dispatchable only after all authority
requirements are satisfied.

## 5. State machine

```text
OBSERVED -> NORMALIZED -> CLASSIFIED -> PROPOSED
  -> AWAITING_AUTHORIZATION (when required) -> AUTHORIZED
  -> QUEUED -> READY -> LEASED -> EXECUTING -> REPORTED
  -> VERIFYING -> VERIFIED_PASS | VERIFIED_FAIL | VERIFIED_UNKNOWN
  -> ASSURING (when material)
  -> READY_FOR_PROMOTION | NOT_READY | MORE_EVIDENCE_REQUIRED
  -> PROMOTION_AWAITING_AUTHORIZATION (if irreversible)
  -> PROMOTED -> SYNCHRONIZED -> CHECKPOINTED -> LEARNED -> CLOSED
```

Exceptional states are `BLOCKED`, `HALTED`, `QUARANTINED`, `EXPIRED`,
`CANCELLED`, `FAILED`, and `SUPERSEDED`.

Transition laws:

1. `AUTHORIZED` requires an explicit artifact or pre-authorized reversible
   policy.
2. An executor cannot move its work directly to `VERIFIED_PASS` or
   `READY_FOR_PROMOTION`.
3. Schedule, timeout, silence, and inferred intent cannot authorize irreversible
   promotion.
4. Every retry creates a linked attempt record.
5. Every correction preserves the original and its correction relationship.
6. `UNKNOWN` and `MORE_EVIDENCE_REQUIRED` are valid outcomes for the current
   gate.

## 6. Authorization boundary

```text
GovernanceDecision
- decision_id
- work_id / action class
- principal or governing policy
- allow | deny | halt | escalate
- exact scope
- expiry
- preconditions
- prohibited actions
- required evidence
- signature/provenance

AssuranceDecision
- assurance_id
- target action
- ready | not_ready | more_evidence_required
- evidence set
- unresolved risks
- confidence statement
- validity window
- reopening conditions
```

Runtime requires both decisions when policy requires both. Assurance does not
grant authority, and Governance does not manufacture evidence.

## 7. Memory and knowledge synchronization

Runtime proposes capture after a material failure, changed belief,
contradiction, repeated investigation, unexpected success, architecture
decision, release/rollback, governance exception, reusable prevention record, or
correction of inherited knowledge.

The Memory Engine selects the minimum fitting record type: Failure Record (FR),
Rumination (RM), Idea Evolution Record (IER), Reasoning Ledger (RL),
Traceable Epistemic Transition capsule (TET), ADR/decision, pattern,
anti-pattern, risk, assumption, experiment, or unexpected-success record.
Verification confirms evidence, Knowledge evaluates relationships and gravity,
and Governance approves changes affecting higher layers. Runtime never promotes
a record to institutional truth.

Every accepted record links to its source event and at least one reuse,
decision, pattern, risk, principle, candidate, implementation, or verification
relationship. Every material record has a review trigger or reversal condition.

## 8. Logical engine APIs

```text
Executive:    submit_intent; materialize_plan; dispatch_ready_work;
              report_execution
Governance:   request_authorization; validate_authorization; halt
Verification: request_verification; get_verification
Assurance:    request_assurance
Memory:       propose_capture; append_memory; schedule_revalidation
Knowledge:    resolve_context; evaluate_gravity;
              evaluate_genome_membership
Evolution:    submit_learning_signal; schedule_candidate_review
```

These are logical contracts, not technology choices. Write APIs return durable
identifiers and provenance; material mutations are append-only or
version-preserving.

## 9. Queue and scheduling policy

Priority is a reasoned tuple covering constitutional/governance urgency, safety,
release blocking, dependency criticality, the cost of missing a deadline,
reversibility, evidence freshness, learning value, and operator priority. A
numeric score may assist but cannot replace rationale.

Blocked high-priority work does not block unrelated ready work. Aging protects
low-priority work from starvation. Governance/security alerts preempt only
within policy. Repeated retries lose priority and escalate rather than loop.

Scheduling classes are one-time, interval, calendar, event-driven,
dependency-driven, review-triggered, expiry-driven, and manual-authorization
continuation.

## 10. Reliability and failure containment

- Assume at-least-once delivery and require stable idempotency keys.
- Use expiring execution leases so a lost executor retains no indefinite
  authority.
- Bound retries by attempts, time, cost, and risk; irreversible retries require
  fresh authorization.
- Quarantine unverifiable identity, schema violations, repository mismatch,
  secret material, contradictory authority, unknown destructive actions,
  missing provenance, and replay outside a validity window.
- If Knowledge, Memory, Verification, Governance, or Assurance is unavailable,
  continue only pre-authorized reversible observation and recording. Stop
  promotion and irreversible action.

## 11. Runtime health

Health states are `HEALTHY`, `DEGRADED`, `BLOCKED`, `UNSAFE`, and `UNKNOWN`.
Minimum indicators include ingestion lag, normalization failures, queue age and
depth, state duration, expired leases, retries, quarantine volume,
authorization/verification latency, synchronization conflicts, checkpoint
freshness, notification acknowledgement, memory reuse, prevented governance
violations, and reviewed alert accuracy.

Running processes alone never establish `HEALTHY`.

## 12. Knowledge Gravity and Engineering Genome

Runtime emits evidence signals for verified reuse, successful prediction,
contradiction, failure prevention, supersession, stale review, and independent
convergence. It does not turn a score into authority. Knowledge proposes gravity
changes with reasons and links; Governance approves promotions affecting
Foundational Concepts, principles, or mandatory patterns.

Runtime records actual use of principles, patterns, anti-patterns, heuristics,
risk tolerances, governance behavior, and verification practices. Genome
membership requires explicit adoption, versioning, evidence, and reversal
conditions.

## 13. TARP-0001 traceability

Every material Runtime decision traces:

```text
Constitution -> Foundational Concepts -> Ontology
-> Architectural Principles/Candidates -> Runtime Contract -> Work Item
-> Implementation -> Verification -> Assurance/Governance -> Memory -> Learning
```

Review asks whether the decision preserves human authority; separates
observation, execution, verification, assurance, and authorization; strengthens
Knowledge Gravity and the Engineering Genome; is reproducible from durable
evidence; contains failures honestly; and is understandable without conversation
history.

## 14. Architectural candidate evidence

- **AC-0003 — Architectural Contracts:** Strengthened because all ten components
  use consistent contract fields.
- **AC-0004 — Separation of Decision and Execution:** Strengthened because
  Governance, Verification, Assurance, and execution remain distinct.
- **AC-0005 — Explicit Relationships:** Strengthened because reconstruction
  requires correlation, causation, provenance, correction, supersession,
  authorization, verification, and learning links.
- **AC-0006 — Semantic Inheritance:** Strengthened but unresolved; common
  obligations reduce duplication only if governed exceptions remain possible
  and ephemeral entities are not forced to carry meaningless fields.

This specification does not promote a candidate.

## 15. Deployment neutrality

Permitted deployments include local single-process development, services,
durable workflow engines, queue/event-bus architectures, managed cloud, and
hybrid human/AI control planes. Technology selection is deferred. Every
implementation must preserve canonical IDs, state transitions, idempotency,
provenance, authorization boundaries, and append-only historical continuity.

## 16. Acceptance criteria

The design passes when:

- component responsibilities and authority are explicit and non-overlapping;
- event and work models are context-complete;
- state transitions prevent self-authorization and self-certification;
- irreversible actions require explicit current authority;
- duplicate events and partial failure degrade safely;
- synchronization preserves conflict and correction history;
- memory capture is triggered without automatic promotion to truth;
- Knowledge Gravity and the Engineering Genome receive evidence-backed signals;
- TARP-0001 traceability is end-to-end;
- no technology is presented as architecturally necessary; and
- implementation can begin without relying on conversation history.

## 17. Open risks and decision

Open risks include unknown event volume and retention cost, unspecified
source-of-truth precedence, multi-tenant identity and authorization, clock skew
and delayed delivery, false precision in priority/gravity models, alert fatigue,
and unselected durable-workflow technology.

Reopen this specification when implementation evidence reveals state ambiguity,
excessive coordination cost, unsafe autonomy, poor recoverability, or inability
to reconstruct decisions from durable records.

**Decision:** Adopt Runtime Domain Specification v1.0 as the
implementation-neutral architectural baseline for Issue #17, subject to
TARP-0001 review and implementation evidence. This document authorizes no code,
deployment, merge, release, secret handling, or irreversible repository action.
