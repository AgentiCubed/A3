# Agentic³ Implementation Blueprint

**Status:** Executable repository plan; no implementation authorization  
**Governing issue:** [#21 — Publish Agentic³ implementation blueprint](https://github.com/AgentiCubed/agenticubed/issues/21)  
**Architecture input:** [#19 — Unified Agentic³ Architecture Specification v2](https://github.com/AgentiCubed/agenticubed/issues/19)  
**Supporting inputs:** [#12 — Institutional memory](https://github.com/AgentiCubed/agenticubed/issues/12), [#16 — Ontology](https://github.com/AgentiCubed/agenticubed/issues/16), and [#17 — Runtime Domain](https://github.com/AgentiCubed/agenticubed/issues/17)

## 1. Purpose, authority, and constraints

This blueprint translates the Unified Agentic³ Architecture v2 into small,
independently releasable repository changes. It defines implementation seams,
not new constitutional authority. Before an implementation phase starts, its
architecture inputs must be merged or reconciled through the repository's
governed review process; an open issue, draft specification, or this blueprint
does not itself authorize execution.

The governing hierarchy is:

`Constitution → Foundational Concepts → Ontology → Architectural Principles → Architectural Contracts → Patterns → Implementations`

AC-0001 Knowledge Gravity and AC-0002 Engineering Genome are adopted
Foundational Concepts. AC-0003 through AC-0006 remain candidates until an
evidence-backed governance decision changes their status. In particular, this
plan uses explicit interfaces and relationships because they make the design
implementable, but does not silently promote Architectural Contracts,
Separation of Decision and Execution, Explicit Relationships, or Semantic
Inheritance.

The following invariants apply to every phase:

1. Governance grants bounded authority; Assurance determines evidence-based
   readiness. Neither substitutes for the other.
2. Runtime may observe, schedule, queue, lease, retry, synchronize, and report
   reversible work. It may not infer approval or authorize an irreversible
   action.
3. Merge, protected-branch push, tag mutation, release publication, history
   rewrite, branch deletion, protection changes, secret rotation, and
   destructive cleanup require a current human authorization artifact.
4. An executor cannot be the sole evaluator of its own material action.
5. Facts, reports, proposals, decisions, authorizations, verification, and
   assurance outcomes remain distinct.
6. Durable history is append-only or version-preserving. Correction,
   contradiction, revocation, and supersession add linked records; they do not
   erase prior state.
7. Provider, queue, workflow, database, graph, and artifact-store products are
   adapters, never constitutional architecture.
8. This workstream changes no product code and makes no Cockpit changes.

## 2. Target repository structure

The first implementation should remain a modular monolith. New Agentic³ code is
isolated behind ports while existing project, orchestration, evaluation, RBAC,
audit, worker, and artifact capabilities are reused through adapters rather
than moved in a risky rewrite.

```text
backend/
  app/
    agentic3/
      contracts/                 # versioned commands, events, decisions, IDs
      ports/                     # Protocol interfaces; no framework imports
      executive/
        intent.py
        planning.py
        governance.py
        orchestration.py
      intelligence/
        verification.py
        memory.py
        knowledge.py
        evolution.py
      assurance/
        service.py
        policy.py
      runtime/
        observer.py
        normalizer.py
        scheduler.py
        queue.py
        dispatcher.py
        monitor.py
        synchronizer.py
        checkpoints.py
        telemetry.py
        notifier.py
        state_machine.py
      adapters/
        persistence/             # SQLAlchemy repositories and outbox
        workflow/                # existing Celery WorkflowEngine adapter
        sources/                 # GitHub/CI/repository adapters, added as needed
        artifacts/               # existing ArtifactStore adapter
    api/v1/routers/agentic3/     # thin authenticated HTTP/SSE controllers
    models/agentic3.py           # ORM mappings only
    schemas/agentic3.py          # HTTP transport schemas only
    workers/agentic3.py          # composition and task entry points only
  alembic/versions/              # additive, reversible schema migrations
  tests/
    unit/agentic3/               # contracts, policies, state machines
    integration/agentic3/        # DB, API, outbox, worker boundary tests
docs/
  agentic3/
    ARCHITECTURE-v2.md
    IMPLEMENTATION-BLUEPRINT.md
  governance/
    ontology/                    # canonical ontology specifications
    knowledge/                   # memory records and Engineering Genome
```

Dependency direction is
`API/workers/adapters → application engines → contracts/ports`. Engine modules
must not import FastAPI, Celery, Redis clients, provider SDKs, or ORM models.
Transactions, transport, scheduling technology, and source integrations remain
edge concerns.

Existing `app/services`, `app/orchestration`, `app/evaluation`,
`app/remediation`, `app/workers`, and `app/core/rbac.py` remain operational.
Agentic³ adapters call them where their current contracts satisfy the new
ports. Replacement happens capability by capability, with characterization
tests, not by directory migration.

Deployment begins with four process boundaries: the existing API process
composes HTTP adapters and engines; the existing worker process composes
Runtime handlers and executors; one scheduler process creates only due work
proposals; and PostgreSQL, the workflow broker, and ArtifactStore remain
infrastructure adapters. Engines are packages, not independently deployable
services. A later split must preserve the same ports, contracts, tenant and
authority checks, outbox/inbox delivery, and failure behavior.

## 3. Ownership and engine-to-module mapping

| Domain / engine | Owned module | Owns | Consumes / emits | Authority boundary |
|---|---|---|---|---|
| Executive / Intent | `agentic3/executive/intent.py` | Objectives, constraints, acceptance criteria | Human intent; `proposed.intent_recorded` | Preserves intent; cannot authorize work or redefine the Principal's intent |
| Executive / Planning | `agentic3/executive/planning.py` | Plans, milestones, tasks, dependencies, risks | Intent; `proposed.plan_materialized` | Decomposes approved intent; cannot redefine success or approve its plan |
| Executive / Orchestration | `agentic3/executive/orchestration.py` | Assignment and bounded execution coordination | Authorized work; dispatch/report events | Cannot authorize irreversible action or certify completion |
| Executive / Governance | `agentic3/executive/governance.py` | Delegations, boundaries, gates, permissions, authorization decisions | Action packets; `governed.allowed|denied|halted|escalated` | Grants only authority held by the Principal/policy; cannot execute work or fabricate evidence |
| Intelligence / Verification | `agentic3/intelligence/verification.py` | Criteria evaluation and Verification Records | Evidence; `verified.pass|fail|unknown` | Criteria are fixed before execution; cannot authorize action or self-verify |
| Intelligence / Memory | `agentic3/intelligence/memory.py` | Capture, classification, provenance, checkpoints, FR/RM/IER/RL/TET records | Runtime capture proposals; `learned.memory_appended` | Records claims and transitions; cannot determine truth, promote knowledge, or confer authority |
| Intelligence / Knowledge | `agentic3/intelligence/knowledge.py` | Semantic queries, contradiction, Knowledge Gravity proposals, Genome membership proposals | Memory/evidence/relationships; proposal events | Cannot ratify, authorize, or automatically promote/demote |
| Intelligence / Evolution | `agentic3/intelligence/evolution.py` | Experiments, candidate and reopening proposals | Learning signals; `proposed.evolution_change` | Proposes reversible review work; cannot amend, deploy, or promote its own proposal |
| Assurance / Assurance | `agentic3/assurance/service.py` | Readiness decisions over evidence, risk, verification, and governance constraints | Verification set and risk set; `assured.ready|not_ready|more_evidence_required` | Cannot execute, mutate evidence, grant authority, or replace human acceptance |

Governance is implemented as a peer engine inside the Executive Domain. If the
canonical architecture later establishes a separate Governance Domain, only
the package composition changes; the governance port and authority boundary do
not.

The complete implementation ownership crosswalk is:

| Engine | Port/API contract | Persistence owner | Required focused tests | Initial process |
|---|---|---|---|---|
| Intent | `submit_intent(IntentV1)` | `agentic3_entities` plus existing Project reference | intent fidelity, provenance, tenant scope | API |
| Planning | `materialize_plan(PlanV1)` | `agentic3_entities`/relationships plus existing Milestone/Task references | deterministic decomposition, DAG, criteria preservation | API |
| Orchestration | `dispatch_ready_work`, `report_execution` | Work Item, lease, transition, existing TaskExecution references | authority/capability, retry, state table | worker |
| Governance | `request_authorization`, `validate_authorization`, `halt` | immutable governance authorizations and AuditEvent | allow/deny/expiry/revoke, scope mismatch, self-escalation | API/worker service |
| Verification | `request_verification`, `get_verification` | immutable Verification Records and evidence edges | fixed criteria, independent verifier, tri-state result | worker |
| Memory | `propose_capture`, `append_memory`, `schedule_revalidation` | memory records/revisions and artifact references | taxonomy, provenance, lifecycle, no auto-promotion | worker/API review |
| Knowledge | `resolve_context`, `evaluate_gravity`, `evaluate_genome_membership` | entities/edges, gravity events, Genome revisions | bounded queries, evidence/reuse, anti-gaming | worker/read API |
| Evolution | `submit_learning_signal`, `schedule_candidate_review` | experiment/candidate entities and proposal events | proposal-only authority, reopening/supersession | worker |
| Assurance | `request_assurance` | immutable Assurance Decisions and evidence/risk edges | ready/not-ready/more-evidence, freshness, no authorization | worker |

### Runtime components

| ID | Component / module | Responsibility and output |
|---|---|---|
| RT-101 | Event Observer / `runtime/observer.py` | Read approved sources and emit raw observations with source identity, timestamps, adapter version, and digest |
| RT-102 | Event Normalizer / `runtime/normalizer.py` | Validate and normalize a source event to `RuntimeEventV1`, or create a quarantine record without inventing facts |
| RT-103 | Scheduler / `runtime/scheduler.py` | Turn approved temporal policies and review triggers into proposed work; report missed schedules |
| RT-104 | Queue Manager / `runtime/queue.py` | Own explainable priority, dependencies, aging, and blocked/quarantined states |
| RT-105 | Dispatcher / `runtime/dispatcher.py` | Validate authority and capability, then issue an expiring `ExecutionLease` and exact executor packet |
| RT-106 | Execution Monitor / `runtime/monitor.py` | Track heartbeat, deadlines, stop conditions, bounded retries, and halt/escalation proposals |
| RT-107 | Synchronizer / `runtime/synchronizer.py` | Compare Runtime with authoritative sources; append reconciliation or contradiction records without silent overwrite |
| RT-108 | Checkpoint Manager / `runtime/checkpoints.py` | Capture context-complete, immutable checkpoints distinguishing facts, inference, decisions, unknowns, and pending authority |
| RT-109 | Telemetry and Health / `runtime/telemetry.py` | Derive health indicators and evidence-safe metrics from transitions |
| RT-110 | Notifier and Escalation Router / `runtime/notifier.py` | Deliver deduplicated decision requests and alerts; silence never becomes approval |

`runtime/state_machine.py` is a shared transition-policy module used by RT-104
through RT-108, not an eleventh autonomous Runtime component. Its exhaustive
allowed/denied transition tests are owned by Queue Manager.

## 4. Contract model

### 4.1 Contract rules

- Public contracts are immutable, versioned Pydantic models in
  `agentic3/contracts`; persistence and HTTP schemas adapt to them.
- Contract evolution is additive within a version. Breaking changes create a
  new version and an explicit translator.
- Commands express requests; events record what occurred. A command is never
  accepted as evidence that its requested outcome occurred.
- Every write returns a durable identifier and provenance.
- Every command carries actor, tenant, correlation, idempotency, and authority
  context. Unknown identity or tenant mismatch is quarantined or denied.
- Contract tests run against every adapter.

### 4.2 `RuntimeEventV1`

Required fields are `event_id`, `event_type`, `schema_version`,
`source_system`, `source_entity_id`, `source_uri`, `source_timestamp`,
`received_timestamp`, `subject_entity_id`, `correlation_id`,
`causation_id`, `payload_digest`, `classification`, `sensitivity`,
`trust_level`, `idempotency_key`, `ontology_relationships`, and
`provenance`. `actor_id`, project/repository scope, and `payload_reference`
are nullable only when the source genuinely cannot supply them.

`classification` is one of `fact`, `report`, `proposal`, `decision`,
`authorization`, `verification`, or `alert`. Event families are
`observed.*`, `proposed.*`, `authorized.*`, `dispatched.*`, `executing.*`,
`reported.*`, `verified.*`, `assured.*`, `governed.*`, `synchronized.*`,
`learned.*`, `failed.*`, and `quarantined.*`.

Payload bytes are not placed on the event bus or in logs. Safe small payloads
may be stored as redacted JSON; larger or sensitive allowed content is stored
through `ArtifactStore` and referenced by digest. Secret material is
quarantined without persisting the secret value.

Delivery is at least once. `(source_system, idempotency_key, schema_version)` is
unique, consumers store an inbox receipt in the same transaction as their
effect, and emitted events use a transactional outbox. Ordering is guaranteed
only per subject through a monotonically increasing subject sequence.

### 4.3 Intent, plan, work, authority, verification, and assurance

`IntentV1` contains the Principal-authored objective, constraints, acceptance
criteria, non-goals, actor/tenant, provenance, and version. `PlanV1` contains
the source intent/version, milestones, tasks, dependencies, risks, preserved
acceptance criteria, assumptions, and proposal provenance. Intent and Plan are
stored as typed `agentic3_entities` with explicit relationships to existing
Project, Milestone, and Task rows during migration; neither contract implies
authorization.

`WorkItemV1` contains a versioned objective, origin event, tenant and
repository scope, allowed/prohibited actions and resources, expected outputs,
acceptance criteria, verification plan, required authority, current
authorization reference, risk class, reasoned priority tuple, dependencies,
deadline/review trigger, eligible capabilities, bounded retry policy, stop
conditions, state history, evidence, and learning references. A Work Item is a
proposal, not authorization.

`ExecutionLeaseV1` contains work and version, executor identity, exact task
packet digest, authorization reference, allowed actions/resources, issued and
expiry times, heartbeat interval, attempt, and revocation state. Expiry or
revocation removes authority to continue.

`GovernanceDecisionV1` contains decision and work/action IDs, Principal or
policy, `allow|deny|halt|escalate`, exact scope, expiry, preconditions,
prohibited actions, required evidence, and signed provenance.

`VerificationRecordV1` contains target, immutable criteria version, independent
verifier, `pass | fail | unknown`, criterion results, evidence references,
environment, tool versions, and timestamp.

`AssuranceDecisionV1` contains target action,
`ready | not_ready | more_evidence_required`, the evaluated evidence set,
unresolved risks, confidence statement, validity window, and reopening
conditions. `ready` is not an authorization.

### 4.4 State machine

The canonical happy path is:

```text
OBSERVED → NORMALIZED → CLASSIFIED → PROPOSED
→ AWAITING_AUTHORIZATION (when required) → AUTHORIZED
→ QUEUED → READY → LEASED → EXECUTING → REPORTED
→ VERIFYING → VERIFIED_PASS | VERIFIED_FAIL | VERIFIED_UNKNOWN
→ ASSURING (when material)
→ READY_FOR_PROMOTION | NOT_READY | MORE_EVIDENCE_REQUIRED
→ PROMOTION_AWAITING_AUTHORIZATION (when irreversible)
→ PROMOTED → SYNCHRONIZED → CHECKPOINTED → LEARNED → CLOSED
```

Exceptional states are `BLOCKED`, `HALTED`, `QUARANTINED`, `EXPIRED`,
`CANCELLED`, `FAILED`, and `SUPERSEDED`. State transition records are
append-only. An executor cannot transition its work to `VERIFIED_PASS`,
`READY_FOR_PROMOTION`, or `PROMOTED`. Timeout, schedule, urgency, silence, and
model confidence cannot cause irreversible promotion.

### 4.5 Logical and HTTP APIs

The architecture-facing ports preserve the Runtime specification:

```text
Executive:    submit_intent, materialize_plan, dispatch_ready_work, report_execution
Governance:   request_authorization, validate_authorization, halt
Verification: request_verification, get_verification
Assurance:    request_assurance
Memory:       propose_capture, append_memory, schedule_revalidation
Knowledge:    resolve_context, evaluate_gravity, evaluate_genome_membership
Evolution:    submit_learning_signal, schedule_candidate_review
```

Initial HTTP transport is under `/api/v1/agentic3`:

| Method and path | Purpose | Access |
|---|---|---|
| `POST /runtime/events` | Idempotently ingest an approved source event | Internal service/source-adapter credential |
| `GET /runtime/events/{id}` | Read event metadata and provenance | Tenant-scoped viewer |
| `POST /work-items` | Create a proposed Work Item | Authorized planner/operator |
| `POST /work-items/{id}/authorization-requests` | Request, not infer, a decision | Authorized actor or Runtime |
| `POST /work-items/{id}/leases` | Dispatch after server-side authority validation | Internal dispatcher |
| `POST /verifications` | Request independent verification | Runtime or authorized reviewer |
| `POST /assurance-decisions` | Evaluate readiness | Assurance service identity |
| `POST /memory/captures` | Propose durable capture | Runtime or contributor |
| `GET /knowledge/entities/{id}/context` | Resolve provenance/impact context | Tenant-scoped reader |

OpenAPI schemas are generated from transport models. Internal service identity,
RBAC, tenant scope, rate limits, and audit apply at the API boundary and are
rechecked by write services. Event publication is the integration boundary;
SSE may expose redacted status projections, but no new Cockpit UI is part of
this plan.

## 5. Persistence and migration

### 5.1 Storage interfaces

Ports are implementation-neutral:

```python
class OntologyRepository(Protocol):
    def get_entity(self, entity_id: str) -> Entity: ...
    def append_relationship(self, relationship: Relationship) -> str: ...
    def traverse(self, query: GraphQuery) -> GraphResult: ...

class MemoryRepository(Protocol):
    def append(self, record: MemoryRecord) -> str: ...
    def history(self, record_id: str) -> list[MemoryRevision]: ...

class KnowledgeRepository(Protocol):
    def context(self, entity_id: str, scope: RelationshipScope) -> KnowledgePacket: ...
    def propose_gravity_event(self, proposal: GravityProposal) -> str: ...
    def propose_genome_revision(self, proposal: GenomeProposal) -> str: ...
```

The first adapter uses the existing PostgreSQL boundary:

- `agentic3_entities`: internal UUID, stable canonical ID, type, lifecycle,
  verification/governance status, provenance, current version, tenant scope;
- `agentic3_relationships`: typed source/target edge, authority, evidence,
  asserted/retracted metadata; append-only;
- `runtime_events` and `runtime_ingest_receipts`: immutable event envelope,
  redacted payload/reference, subject sequence, deduplication;
- `runtime_work_items` plus `runtime_work_item_transitions`: current projection
  plus append-only state history;
- `execution_leases`: attempt, exact scope, authorization, expiry, heartbeat,
  revocation;
- `governance_authorizations`, `verification_records`,
  `assurance_decisions`: immutable decision/evidence records;
- `memory_records` and `memory_revisions`: canonical record type, content
  reference, provenance, validation lifecycle, reopening condition;
- `gravity_events`: evidence-backed changes; no mutable aggregate is the source
  of truth;
- `genome_memberships` and `genome_membership_revisions`: explicit, versioned,
  reversible membership independent of gravity;
- `runtime_checkpoints`: immutable state/reference manifests;
- `agentic3_outbox` and consumer inbox receipts: reliable publication.

Current Project, Task, TaskExecution, Evaluation, Approval, Artifact, and
AuditEvent rows remain systems of record during migration. Agentic³ entities
reference them by stable typed reference. Existing UUID primary keys remain;
canonical IDs such as `FR-NNNN` are separately unique in their namespace and
tenant. A graph database, vector database, and event broker are not needed to
implement ontology traversal, provenance, contradiction, or impact analysis
at initial scale.

### 5.2 Integrity and retention

- Foreign keys, tenant checks, type/cardinality validation, acyclic `PART_OF`,
  valid lifecycle transitions, and authority-chain validation are enforced in
  the service and database where practical.
- Evidence, events, decisions, relationships, transitions, revisions, and
  gravity events reject update/delete at application and database layers.
- Operational projections may be rebuilt from append-only history.
- Retention is class-specific. Audit/evidence metadata and digests outlive
  disposable payload bodies. A retention policy must be approved before any
  purge job exists.
- Queries are bounded by tenant, relationship types, depth, and result count.
  Full unbounded graph traversal is prohibited.

### 5.3 Expand-and-contract migration

1. **Prerequisite:** reconcile the v2, ontology, memory, and Runtime design
   sources; record any implementation choice that materially changes data
   ownership as an ADR/TARP review.
2. **Expand:** add tables, constraints, repositories, and feature flags without
   changing existing reads or writes.
3. **Backfill:** create stable references and relationship edges from existing
   rows in deterministic, restartable batches; store source IDs and digests.
4. **Shadow:** emit outbox events and build Agentic³ projections while existing
   behavior remains authoritative. Compare counts, state, tenant scope, and
   digests.
5. **Cut over per capability:** enable one engine/tenant at a time only after
   parity, contract, migration, and rollback tests pass.
6. **Contract:** retire duplicate paths only after at least one release of
   observability and a separate authorization. Never delete historical source
   records as part of cutover.

Every migration supplies downgrade behavior when data-safe. If a schema cannot
be safely downgraded, rollback disables new readers/writers and restores the
prior application while retaining inert additive tables.

## 6. Runtime worker and scheduler design

The API records commands and commits outbox events; it does not perform durable
work inline. A worker claims outbox/inbox records, normalizes events, advances
valid state transitions, and invokes engine ports. A scheduler creates due
proposals from database-backed schedules and review triggers. The existing
Celery/Redis implementation may be the first `WorkflowEngine` adapter, but no
domain or contract imports Celery and no guarantee depends on Redis alone.

Worker requirements:

- at-least-once safe handlers with transactional inbox deduplication;
- short database transactions and compare-and-swap on Work Item version;
- expiring, renewable leases bound to executor and authorization;
- bounded retries by attempts, elapsed time, cost, and risk;
- fresh human authorization for every retry of an irreversible action;
- heartbeat loss yields unknown until timeout, then expiry/escalation, never a
  fabricated failure or success;
- dead-letter/quarantine for identity ambiguity, schema failure, tenant or
  repository mismatch, secret detection, contradictory authority, unknown
  destructive action, missing provenance, or stale replay;
- graceful degradation: if Governance, Verification, Assurance, Memory, or
  Knowledge is unavailable, only pre-authorized reversible observation and
  recording continue; dispatch/promotion stops.

Priority is an explainable tuple: governance urgency, safety/security impact,
release blocking, dependency criticality, deadline cost, reversibility,
evidence freshness, learning value, and operator priority. Aging prevents
starvation; blocked urgent work does not block unrelated ready work; repeated
retry lowers priority and escalates. Supported schedule classes are one-time,
interval, calendar, event-, dependency-, review-, and expiry-driven, plus
manual continuation after authorization.

The approved queue-policy version supplies deterministic comparison rules;
Runtime does not invent weights. Governance and safety constraints are hard
precedence, readiness is required, and the remaining dimensions are compared
in the policy's recorded order with age then stable Work Item ID as tie
breakers. A numeric model may be proposed only after measured evidence and
cannot override those constraints.

## 7. Ontology, Memory, and Knowledge implementation

### 7.1 Ontology

The shared semantic model covers Actor, System, Knowledge, Artifact, Evidence,
Governance, and Temporal entity families. Relationships use a controlled,
versioned vocabulary grouped into authority/governance, execution,
evaluation/verification, knowledge/traceability, and structure/dependency.
Each edge records source, target, assertion actor/time, authority, and required
evidence. Generic links are accepted only when no specific relation fits.

Initial queries must answer provenance, authority chain, impact, contradiction,
reuse, supersession, TARP traceability, and current Genome membership. SQL
adjacency queries are sufficient first. `OntologyRepository` permits a later
graph adapter if measured query cost justifies it.

### 7.2 Memory

Working memory remains ephemeral. Project memory is durable but workstream
scoped. Institutional memory contains validated reusable records. Evolution
memory preserves before/after belief and authority changes; it is a history
rule, not a separate silo.

The canonical durable types are Failure Record (FR), Rumination (RM), Idea
Evolution Record (IER), Reasoning Ledger (RL), Traceable Epistemic Transition
(TET), Decision/ADR, Pattern, Anti-pattern, Risk, Assumption, Experiment, and
Unexpected Success Record. Lifecycle is
`Draft → Active → Validated → Superseded | Retired`. Runtime may propose
capture; the Memory Engine selects the smallest fitting type and preserves
provenance. No automated process creates a Pattern from one event or promotes
a memory to institutional truth.

The repository remains the human-reviewable canonical representation for
governance and knowledge documents. Database records index and link those
artifacts by path, commit, digest, and canonical ID; they do not silently
rewrite files.

### 7.3 Knowledge Gravity and Engineering Genome

Gravity levels are `observation → lesson → pattern → principle → foundational`.
Each `GravityEvent` links inspectable evidence or independent reuse and records
prior/new level. Self-citation does not increment reuse. Contradiction,
disconfirmed experiment, attributable failure, and unbounded exception can
propose demotion. Promotion to foundational always requires an explicit
Principal-ratified governance decision; no score causes promotion.

Genome membership is explicit and independent of gravity. A membership record
contains element type, status, basis, evidence, member-since date, removal
conditions, and append-only revision history. Status changes
`active|under_review|suspended|removed` and reinstatement require the named
human/governance authority. Phase 4 implements manual proposals and review
queues before any automation is considered.

## 8. Governance, verification, assurance, and security gates

### 8.1 Enforcement points

| Point | Required enforcement |
|---|---|
| HTTP/source ingress | Authenticate source, resolve actor/tenant, validate schema and signature, redact, deduplicate, quarantine ambiguity |
| Intent/plan creation | Preserve Principal input, constraints, acceptance criteria, provenance, and TARP links |
| Work Item readiness | Dependencies met; exact scope, risk, criteria, stop conditions, and authority requirements present |
| Dispatch | Current authorization covers exact action/resource; executor capability and tenant match; lease is bounded |
| Tool invocation | Existing default-deny permission and sensitivity checks; resolve secrets by reference only |
| Execution | Lease/authorization still valid; heartbeat and stop conditions enforced; append evidence |
| Verification | Criteria version predates result; verifier independent; evidence inspectable; pass/fail/unknown recorded |
| Assurance | Verification set complete, risks explicit, evidence fresh, validity/reopening recorded |
| Irreversible action | Human authorization is current and exact; Assurance ready when policy requires; revalidate immediately before side effect |
| Synchronization | Source precedence explicit; contradictions and corrections preserved |
| Knowledge/Genome change | Evidence-backed proposal; required reviewer/Principal decision; no automatic higher-layer promotion |

The side-effect adapter is the final hard control. Even if an upstream service
is compromised, it rejects an irreversible call without the exact,
unexpired, unrevoked human authorization and required Assurance decision.
Runtime cannot mint either artifact.

### 8.2 Measurable release gates

An implementation phase cannot release until every gate applicable to the
capabilities introduced or exercised by that phase passes; later-capability
gates are not prerequisites for an earlier isolated slice:

- 100% of public contract examples pass schema and backward-compatibility
  tests;
- duplicate-event and replay tests produce exactly one material effect;
- 100% of state transitions are covered by allowed/denied table tests;
- all tested unauthorized, expired, wrong-tenant, wrong-repository, and
  self-escalation attempts are denied and audited;
- every irreversible-action test fails closed without an exact human
  authorization; silence and timeout tests never approve;
- executor/evaluator collision tests are rejected;
- every Verification and Assurance decision references its criteria/evidence
  and returns the allowed tri-state outcome;
- migration upgrade, deterministic backfill, restart, and rollback/disable
  drills pass on a production-shaped fixture;
- audit reconstruction can reproduce a sampled Work Item's actor, authority,
  transitions, evidence, verification, assurance, and outcome;
- secret scanning and redaction fixtures show no secret value in event,
  payload, log, audit, checkpoint, or artifact metadata;
- phase-specific latency/error budgets are defined from baseline measurements,
  not invented targets.

Significant architecture phases also require a context-complete TARP review and
independent review under the governance playbook.

### 8.3 Security and secrets boundaries

Existing organization/project RBAC and repository scoping remain mandatory.
Service and worker identities are distinct from user tokens. Agent identities
cannot grant permissions, expand scope, disable controls, issue Governance or
Assurance decisions, or alter their own delegation.

Secrets live only in environment/secret-manager adapters and are referenced by
opaque key. Resolution occurs at the outbound adapter after authorization and
immediately before use; plaintext is never passed through an event, Work Item,
prompt context, memory, knowledge edge, checkpoint, log, or audit record.
Source webhook signatures are verified before payload processing. Logs and
audit use allowlisted fields plus existing redaction. Artifact access uses
tenant-scoped opaque IDs, content digests, least privilege, and short-lived
retrieval authorization.

## 9. Observability and audit evidence

Every log, metric, and trace binds `request_id`, `correlation_id`,
`causation_id`, tenant, subject, Work Item, attempt, lease, actor, component,
contract version, and outcome where applicable. Payloads, prompts, tokens, and
secret values are excluded.

Minimum health indicators are ingestion lag, normalization/quarantine rate,
queue depth/age, state duration, expired leases, retries, authorization,
verification and assurance latency, synchronization conflicts, checkpoint
freshness, notification acknowledgement, memory capture/reuse, prevented
governance violations, and reviewed alert false positives/negatives. Process
uptime alone cannot report `HEALTHY`. Component health is `HEALTHY`,
`DEGRADED`, `BLOCKED`, `UNSAFE`, or `UNKNOWN`.

An audit evidence bundle for a material action contains immutable source event,
intent/plan and acceptance criteria, Work Item versions, authority request and
decision, lease and executor packet digest, attempt/transition history,
artifact digests, independent Verification Record, Assurance decision when
required, final human authorization for irreversible promotion,
synchronization result, checkpoint, and memory/learning references. Bundle
generation is a read-only projection; source records remain canonical.

## 10. Phased delivery plan

Each phase is feature-flagged, independently testable, deployable, and
reversible without requiring a later phase.

### Phase 0 — Reconcile contracts and governance inputs

**Build:** Merge or explicitly reconcile v2, ontology, memory, and Runtime
sources; record contract examples, authority matrix, action classification,
source precedence, retention policy, implementation ADRs, and a
Principal-ratified reversible-work standing policy as a versioned governance
decision under `docs/governance/decisions/`.

**Acceptance:** No conflicting engine definition; all candidate/adopted statuses
are explicit; every contract has an owner and version; TARP review complete;
links and glossary are context-complete.

**Release:** Documentation/specification release only.

### Phase 1 — Event ledger vertical slice

**Build:** `RuntimeEventV1`, observer/normalizer service, `runtime_events`,
ingest receipts and outbox, one internal ingest/read API, append-only guards,
deduplication/quarantine, contract/unit/integration tests, and metrics.

**Acceptance:** One approved synthetic source event can be ingested twice with
one stored effect, queried with provenance, safely quarantined on ambiguity,
and reconstructed from audit. No scheduler, Work Item, external source
adapter, autonomous action, or Cockpit change.

**Release:** Disabled by default; enable for a test tenant/source.

This is the first implementation PR. It deliberately excludes queues, agents,
Memory promotion, Knowledge scoring, Genome automation, and side effects, so it
fits a focused review and can be removed by disabling one route/worker flag.

### Phase 2 — Reversible Runtime coordination

**Build:** Work Item and transition ledger, scheduler, queue policy, dispatcher,
execution leases, monitor, checkpoints, existing WorkflowEngine adapter, and
one deterministic reversible executor.

**Acceptance:** Duplicate delivery, clock skew, lost heartbeat, bounded retry,
starvation, dependency, cancellation, expiry, quarantine, and adapter outage
tests pass; no irreversible action can be represented as pre-authorized.
Dispatch names a pre-approved, reversible standing policy as its authorization
basis. Runtime cannot create or broaden that policy, and discretionary or
irreversible work remains undispatchable until Phase 3 Governance exists. At
deployment, an operator registers the Phase 0 governance decision's stable ID,
version, digest, scope, and expiry; the dispatcher verifies that artifact
through a read-only policy adapter before issuing a lease.

**Release:** One reversible work class and tenant; existing task execution
remains authoritative until shadow parity is demonstrated.

### Phase 3 — Governance, Verification, and Assurance gates

**Build:** Authorization, independent Verification, Assurance tri-state,
side-effect guard, synchronizer, notifier/escalation, and audit evidence bundle.

**Acceptance:** All measurable gates in §8.2 pass; final side-effect guard fails
closed; authorization expiry/revocation is immediate; Governance and Assurance
outages permit observation only.

**Release:** Human-authorized pilot. Irreversible adapters remain disabled
until a separate action-specific authorization and rollback drill.

### Phase 4 — Ontology, Memory, and Knowledge foundations

**Build:** Entity/relationship repositories, bounded canonical queries, memory
index and manual capture workflow, GravityEvent proposals, Genome membership
proposals/revisions, review scheduling, and repository artifact linking.

**Acceptance:** Provenance, authority, contradiction, impact, supersession,
reuse, traceability, and Genome queries pass fixtures; one FR/RL lifecycle and
one manual gravity/genome review are reconstructable; no automatic promotion.

**Release:** Read-only knowledge queries first, then human-reviewed writes.

### Phase 5 — Evolution proposals and governed learning

**Build:** Experiment, candidate, reopening, and learning-signal proposals;
review queues; post-implementation comparison of predicted/observed results.

**Acceptance:** Proposals cannot ratify, amend, deploy, or promote themselves;
reopening preserves prior authority/history; candidate status changes require
the canonical governance lifecycle and evidence.

**Release:** Proposal-only mode. Autonomous constitutional or foundational
change remains permanently out of scope.

### Phase 6 — Scale only from evidence

**Build if measured:** alternate workflow/event/graph/artifact adapters,
partitioning, archival, or separate service deployments.

**Acceptance:** Adapter contract parity, replay/migration drill, no authority
boundary regression, and measured benefit exceeding operational cost.

**Release:** One adapter or deployment boundary at a time with dual-run and
rollback.

## 11. Build versus defer

| Build now / early | Defer until evidence | Reason |
|---|---|---|
| Versioned contracts, ports, IDs, provenance | General plugin framework | Concrete second adapters must reveal the useful seam |
| PostgreSQL event/edge ledger and outbox | Graph/vector database | Initial canonical queries are bounded and relational |
| Existing WorkflowEngine adapter | Workflow-vendor migration | Replace only on measured durability/operability gap |
| Human-reviewed gravity/genome proposals | Numeric ranking or automatic promotion | Prevent scoring theater and preserve authority |
| One reversible executor/source | Broad external integrations | Minimize attack and failure surface |
| Append-only audit and evidence bundles | Full event sourcing of legacy domains | Avoid rewriting stable existing behavior |
| Internal API and redacted SSE contract | Cockpit or other UI work | Explicit non-goal; API is independently useful |
| Deterministic rules and independent verification | Model-only verification/assurance | Models may assist but cannot be sole evidence |
| Single-process/service modular monolith | Microservice decomposition | Boundaries are code-level until scale data justifies operations |
| Explicit human authorization | Autonomous irreversible actions | Permanently prohibited, not a backlog item |

## 12. Risk register

| Risk | Signal | Mitigation / owner decision |
|---|---|---|
| Parallel draft specifications conflict | Same engine/entity has different semantics | Phase 0 reconciliation; canonical source and status recorded before code |
| Ontology cannot represent a later engine | Forced generic fields/links | Type-completeness review and authorized ontology revision |
| Knowledge Gravity becomes arbitrary scoring | Counts lack independent evidence | Append-only evidence events, anti-self-citation, manual review, no score promotion |
| Genome becomes aspirational or irreversible | Membership lacks basis/removal conditions | Explicit evidence, governance basis, versioned reversible status |
| Broken traceability | Implementation has no navigable higher-layer/evidence chain | Release-gate trace query; register and block on material gaps |
| Event duplication or reordering corrupts state | More than one effect or invalid transition | Stable idempotency, inbox/outbox, subject sequence, version checks |
| Source precedence causes silent overwrite | GitHub/Git/CI/memory disagree | Approved precedence policy; contradiction record; human resolution |
| Tenant or repository confusion | Cross-scope identifier appears in a packet | Scope in every contract/query; hard mismatch quarantine |
| Lease/authorization survives loss or expiry | Work continues after boundary ends | Short leases, revalidation at side effect, revocation checks |
| Secret enters durable evidence | Scanner/redaction fixture detects value | Quarantine before persistence, references only, purge incident procedure |
| Alert fatigue | Low acknowledgement/actionability | Deduplication, digests, urgency rationale, reviewed alert quality |
| Event retention cost grows unexpectedly | Volume/storage budget exceeded | Class retention, digest-only archival, payload separation; no evidence purge without policy |
| Workflow/graph vendor lock-in | Domain imports vendor APIs | Ports, contract suites, adapter-owned configuration |
| Legacy/new projections diverge | Shadow comparison mismatch | Capability-level cutover, deterministic backfill, retain legacy authority |
| Unsafe degraded operation | Runtime dispatches while a control is unavailable | Dependency health gate; observation/recording only |

Reopen this blueprint when implementation evidence shows state ambiguity,
excessive coordination cost, unsafe autonomy, poor recoverability, inability to
reconstruct decisions, an unmappable engine type, a new Foundational Concept,
or a constitutional change affecting authority/evidence.

## 13. Rollback plan

Rollback is capability-level, not destructive:

1. Disable ingress, scheduler, dispatch, knowledge-write, or side-effect feature
   flags independently.
2. Stop issuing leases; revoke or let active reversible leases expire. Halt
   irreversible work and require a new human decision.
3. Drain or preserve inbox/outbox records; never drop them to make rollback
   appear clean.
4. Restore legacy reads/writes as authoritative; keep Agentic³ projections
   read-only for diagnosis.
5. Deploy the prior application. Additive tables remain inert when downgrade
   would discard evidence.
6. Reconcile all in-flight IDs, transitions, artifacts, and authorization
   outcomes; append correction/supersession records.
7. Capture a checkpoint, Failure Record when warranted, verification evidence,
   and reopening conditions before retrying rollout.

Each phase's release packet names its flags, last safe schema, in-flight work
policy, adapter rollback, data reconciliation query, responsible human, and
maximum rollback decision time. A rollback exercise is acceptance evidence,
not an optional operational note.

## 14. Definition of complete

The blueprint is implemented only when every engine and Runtime component has
owned code, a tested port, a persistence owner, emitted/consumed contracts,
health evidence, and an explicit authority boundary; every phase has passed its
release gate and rollback drill; Memory, Knowledge Gravity, and Engineering
Genome operate through inspectable human-reviewed records; and no irreversible
action can occur without current, exact human authorization.
