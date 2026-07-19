<<<<<<< HEAD
# Unified Agentic³ Architecture Specification v2

**Status:** Proposed canonical architecture  
**Version:** 2.0-draft  
**Governing issue:** [#19 — Publish Unified Agentic³ Architecture Specification v2](https://github.com/AgentiCubed/agenticubed/issues/19)  
**Scope:** Implementation-neutral architecture; this document authorizes no product code, deployment, vendor selection, candidate promotion, or irreversible action.

## 1. Mission and architectural promise

Agentic³ is an engineering intelligence system that coordinates human and
autonomous contributors through planned, reviewable, evidence-backed work. It
turns intent into bounded work, preserves authority with the responsible
Principal, independently verifies material claims, remembers how knowledge
changed, and improves through governed learning.

The architecture promises that:

- authority is explicit, bounded, revocable, and traceable to a Principal;
- planning, authorization, execution, verification, assurance, and acceptance
  remain distinguishable;
- durable claims preserve provenance, contradiction, uncertainty, and history;
- continuous operation never turns scheduling, silence, confidence, or
  technical capability into permission;
- implementation choices remain replaceable when they preserve the contracts
  and invariants in this specification.

## 2. Authority, status, and source set

This specification is subordinate to the
[Constitution v1.0](../governance/constitution/Constitution-v1.0.md) and
[Amendment A-0001](../governance/constitution/Amendment-A-0001.md). The
Constitution governs enduring authority, evidence, Verification, bounded
autonomy, Halt, and amendment. This document defines subordinate architecture;
it does not reinterpret or rewrite the Constitution.

The consolidated design inputs are:

- [Issue #12 — Institutional memory system](https://github.com/AgentiCubed/agenticubed/issues/12);
- [Issue #16 — Ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16);
- [Issue #17 — Runtime Domain](https://github.com/AgentiCubed/agenticubed/issues/17);
- AC-0001 Knowledge Gravity and AC-0002 Engineering Genome;
- candidate AC-0003 Architectural Contracts;
- candidate AC-0004 Separation of Decision and Execution;
- candidate AC-0005 Explicit Relationships;
- candidate AC-0006 Semantic Inheritance; and
- TARP-0001, the Traceable Architecture Review Process.

The [implementation blueprint workstream (Issue #21)](https://github.com/AgentiCubed/agenticubed/issues/21)
is the intended downstream mapping from this architecture to modules, APIs,
persistence, tests, deployment boundaries, and release gates. Until that
blueprint is reviewed, no technology choice is implied by this specification.

## 3. Governing hierarchy

The canonical architecture hierarchy is:

```text
Constitution
  → Foundational Concepts
    → Ontology
      → Architectural Principles
        → Architectural Contracts
          → Patterns
            → Implementations
```

The Constitution grants or constrains authority. Foundational Concepts guide
every subsystem. The Ontology defines what entities and relationships mean but
does not confer authority. Principles state durable design rules. Contracts
declare subsystem obligations. Patterns offer evidenced reusable approaches.
Implementations are replaceable realizations.

### 3.1 Upward Compatibility Rule

A lower layer may refine a higher layer but may not contradict it without an
explicit, evidence-backed supersession decision made under valid authority. A
constitutional conflict is a hard stop unless the constitutional amendment
process is invoked.

Document existence, age, popularity, graph centrality, and model confidence do
not create authority. Authority requires an active constitutional, ratification,
governance, delegation, or approval relationship.

## 4. Foundational Concepts

### 4.1 AC-0001 — Knowledge Gravity

Knowledge gains or loses justified influence through evidence, successful
reuse, predictive value, contradiction, failed application, staleness, and
supersession—not through author, age, repetition, or an opaque score.

Every subsystem must:

1. emit provenance-preserving evidence about outcomes and reuse;
2. expose contradictions, failed applications, and uncertainty;
3. identify knowledge it consumed and outcomes it informed;
4. support review, demotion, supersession, and retirement;
5. avoid treating a numeric weight as authority or truth.

Gravity review returns an evidence-backed rationale and one of: retain,
increase influence, decrease influence, promote, constrain, revalidate,
supersede, retire, or request more evidence. Governance alone authorizes a
promotion that changes a mandatory or higher architectural layer.

### 4.2 AC-0002 — Engineering Genome

The Engineering Genome is the explicit, versioned, reversible set of principles,
patterns, anti-patterns, heuristics, governance rules, verification practices,
architectural preferences, values, and risk tolerances that characterize how
Agentic³ engineers systems.

Every subsystem must:

1. declare which Genome members it applies or challenges;
2. record observed use rather than aspirational compliance;
3. preserve adoption evidence, scope, version, review trigger, and reversal path;
4. emit learning signals when a member is strengthened, weakened, introduced,
   or made obsolete;
5. preserve prior Genome versions when membership changes.

Genome membership never substitutes for constitutional authority, current
evidence, or a bounded authorization.

## 5. Architectural candidates

The following statuses are intentionally conservative. Evidence generated by
Memory, Ontology, and Runtime design strengthens these candidates but does not
promote them.

| ID | Candidate | Status in this specification | Meaning and current evidence |
|---|---|---|---|
| AC-0003 | Architectural Contracts | Proposed candidate | Repeated subsystem descriptions benefit from explicit mission, inputs, outputs, dependencies, authority, constraints, evidence, and learning obligations. |
| AC-0004 | Separation of Decision and Execution | Proposed foundational candidate | Distinct planning, authorization, execution, Verification, Assurance, and acceptance boundaries prevent self-authorization and self-certification. |
| AC-0005 | Explicit Relationships | Proposed candidate | Traceability, provenance, authority, contradiction, impact, Knowledge Gravity, and Genome membership require typed semantic edges. |
| AC-0006 | Semantic Inheritance | Proposed candidate | Shared identity, provenance, lifecycle, and governance metadata reduce duplication, but specialized obligations and governed exceptions must remain explicit. |

No statement elsewhere in this document changes these statuses. Promotion
requires the lifecycle and evidence gates in section 15.

## 6. Canonical ontology

Every durable, addressable object is an `Entity` with:

- a stable identifier, canonical name, type, namespace, and aliases;
- a lifecycle state and current immutable version reference;
- creation and provenance references;
- Verification and governance status where applicable;
- authority references where authority is claimed; and
- explicit, typed semantic relationships.

Identity persists across versions. Versions are append-only historical nodes.
Correction creates a new version linked to the prior version; it does not erase
the earlier state. Time-dependent queries must support an `as_of` boundary.

### 6.1 Entity families

| Family | Canonical members |
|---|---|
| Actor | Human, AI agent, organization, service identity |
| System | Domain, engine, Runtime component, tool, repository, workflow |
| Governance | Constitution, amendment, authority grant, permission, policy, standard, procedure, gate, approval |
| Knowledge | Observation, assumption, claim, finding, decision, lesson, pattern, anti-pattern, heuristic, principle, Foundational Concept, candidate, risk, experiment, and institutional memory record |
| Artifact | Issue, pull request, commit, branch, tag, release, source file, ADR, design ledger, report, checkpoint |
| Evidence | Test, CI, review, Verification, or Assurance result; metric; log record |
| Work | Objective, plan, milestone, task, work item, Runtime event, execution |
| Temporal | Lifecycle state, transition, version, validity interval, review trigger |

Facts, reports, interpretations, hypotheses, decisions, authorizations,
Verification results, Assurance results, and unknowns are distinct entities or
classifications. One must not be silently converted into another.

### 6.2 Relationships

Relationships are first-class, typed, attributable, versioned entities. Each
records its stable ID, source, predicate, target, evidence, asserting actor,
authority basis when applicable, validity interval, epistemic confidence when
applicable, lifecycle state, and supersession link.

The controlled relationship classes include:

- **structural:** `is_a`, `part_of`, `contains`, `depends_on`,
  `exposes_contract`, `implements`, `instantiates`;
- **authority:** `governs`, `authorizes`, `prohibits`, `delegates_to`,
  `requires_gate`, `ratifies`, `supersedes`;
- **epistemic:** `observes`, `asserts`, `supports`, `contradicts`, `verifies`,
  `assures`, `derives_from`, `interprets`, `reopens`;
- **work:** `defines`, `decomposes_into`, `assigned_to`, `executes`, `produces`,
  `consumes`, `blocks`, `satisfies`, `fails`;
- **learning:** `records`, `extracts`, `promotes`, `demotes`, `strengthens`,
  `weakens`, `contributes_to_genome`, `removed_from_genome`, `learned_from`.

An assignment identifies an executor but does not authorize the action.
Verification establishes a result against criteria but does not authorize
execution. Assurance evaluates readiness but does not grant authority.

### 6.3 Graph integrity laws

1. Every durable entity and relationship has one stable canonical identity.
2. Material claims, decisions, grants, and transitions link to actor and evidence.
3. Authority requires a valid authority relationship; storage is not authority.
4. An Executor cannot be the sole Evaluator or assurer of its Material Action.
5. Supersession ends current effect without deleting history.
6. Every edge satisfies its allowed source and target types.
7. Contradictory knowledge remains visible until resolved under valid authority.
8. Lower layers obey the Upward Compatibility Rule.
9. Durable decisions are reconstructable without conversational memory.
10. Epistemic states remain distinct.
11. Delegation records issuer, recipient, scope, expiry or revocation condition,
    and prohibited actions.
12. Genome membership is versioned and reversible.
13. Every gravity change cites its evidence-producing event.
14. Durable architecture artifacts without meaningful semantic edges are
    flagged as orphans.
15. Supersession, precedence, plan decomposition, authority, and inheritance
    graphs are acyclic.

### 6.4 Query contract

The Knowledge Engine must support explainable provenance, authority, impact,
contradiction, reuse, gravity, Genome, traceability, historical reconstruction,
and candidate-promotion queries. Material results identify the versions and
edges traversed, temporal and authority boundaries, evidence included and
excluded, unresolved contradictions, and result rationale.

Result states are `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`,
`CONFLICT`, `STALE`, `UNKNOWN`, and `NOT_APPLICABLE`. Ranking or confidence
must not convert `UNKNOWN` or `CONFLICT` into a positive claim.

## 7. Domains and engine ownership

Each engine has exactly one owning domain. Cross-domain calls occur through
contracts; they do not transfer ownership or authority.

| Domain | Owned engines/components | Domain responsibility |
|---|---|---|
| Executive | Intent, Planning, Orchestration, Governance | Translate Principal intent into bounded plans, assignments, and governing decisions. |
| Intelligence | Verification, Memory, Knowledge, Evolution | Evaluate evidence, preserve history, derive reusable knowledge, and propose evidence-backed change. |
| Assurance | Assurance Engine | Independently determine whether evidence and unresolved risk are sufficient for a proposed Material Action. |
| Runtime | Observer, Normalizer, Scheduler, Queue Manager, Dispatcher, Execution Monitor, Synchronizer, Checkpoint Manager, Telemetry and Health, Notifier and Escalation Router | Continuously observe and coordinate authorized work while preserving state, evidence, and safety boundaries. |

No engine appears in more than one domain. A deployment may combine components
physically, but it must preserve their logical contracts, evidence, and
separation-of-authority constraints.

## 8. Engine architectural contracts

### 8.1 Executive Domain

**Intent Engine**

- **Mission:** capture Principal objectives, constraints, success conditions,
  and authority source without redefining them.
- **Produces:** versioned objectives, constraints, and acceptance criteria.
- **Must not:** authorize execution or alter Principal intent.

**Planning Engine**

- **Mission:** decompose authorized intent into plans, milestones, tasks,
  dependencies, risks, and Verification plans.
- **Produces:** proposed, versioned plans and work definitions.
- **Must not:** redefine success, grant authority, or approve its own plan.

**Orchestration Engine**

- **Mission:** coordinate assignments and workflows that realize an authorized
  plan.
- **Produces:** assignments, workflow state, and execution coordination records.
- **Must not:** authorize irreversible action or certify completion.

**Governance Engine**

- **Mission:** resolve active authority and policy, issue bounded decisions,
  enforce gates, and preserve Delegation, prohibition, Halt, promotion, and
  supersession decisions.
- **Produces:** allow, deny, Halt, or escalate decisions with exact scope,
  issuer, recipient, expiry, preconditions, prohibitions, and required evidence.
- **Must not:** execute governed work, fabricate evidence, or treat Assurance as
  authority.

### 8.2 Intelligence Domain

**Verification Engine**

- **Mission:** evaluate inspectable evidence against pre-established criteria.
- **Produces:** pass, fail, or unknown results, scope limits, and contradiction
  links.
- **Must not:** authorize action, change criteria after observing results, or
  rely solely on an Executor's self-attestation.

**Memory Engine**

- **Mission:** capture context-complete events, decisions, checkpoints, record
  versions, provenance, and historical continuity.
- **Produces:** durable memory records and links from source events to learning.
- **Must not:** determine truth, promote knowledge, resolve authority, or erase
  inconvenient history.

**Knowledge Engine**

- **Mission:** retrieve and relate validated memory; identify contradiction,
  reuse, impact, staleness, gravity changes, and Genome membership.
- **Produces:** explainable knowledge packets and evidence-backed proposals.
- **Must not:** ratify, authorize, or silently promote a candidate or claim.

**Evolution Engine**

- **Mission:** turn failures, successes, experiments, metrics, contradictions,
  and Genome gaps into reviewable change or reopening proposals.
- **Produces:** candidate, experiment, ontology, principle, Pattern, and Genome
  change proposals.
- **Must not:** deploy its proposal, amend the Constitution, or mutate a higher
  layer directly.

### 8.3 Assurance Domain

**Assurance Engine**

- **Mission:** determine whether the available Verification results, evidence,
  authority context, risk, contradiction, and uncertainty are sufficient to
  proceed with a specified Material Action.
- **Produces:** `ready`, `not_ready`, or `more_evidence_required`, including the
  evidence set, unresolved risks, validity window, and reopening conditions.
- **Must not:** execute, mutate evidence, grant authority, accept work for the
  Principal, or replace independent Verification.

Governance answers **may this action occur and within what Boundary?** Assurance
answers **is the evidence sufficient to take this action now?** Runtime enforces
both when policy requires both.

## 9. Runtime Domain

Runtime is the continuously operating coordination layer. It observes events,
creates and prioritizes work, leases authorized tasks, monitors execution,
synchronizes authoritative state, records checkpoints, emits telemetry, and
routes decisions to authorized Principals.

> Runtime may initiate and coordinate reversible workflows, but it may not
> authorize or perform irreversible actions without an explicit Governance
> authorization and, where required, a current Assurance decision.

Irreversible actions include merge, protected-branch push, tag creation,
deletion or movement, release publication, history rewrite, branch deletion,
protection or ruleset change, secret rotation, and destructive cleanup.

### 9.1 Runtime component boundaries

| Component | Responsibility | Prohibited shortcut |
|---|---|---|
| Event Observer | Preserve source identity and detect approved events. | Treat observation as truth or authority. |
| Event Normalizer | Validate and classify events without inventing missing facts. | Coerce ambiguous events instead of quarantining them. |
| Scheduler | Materialize due, pre-authorized reversible work and review triggers. | Convert a schedule into permission. |
| Queue Manager | Explainably order work and track dependencies, blocks, and aging. | Broaden scope or let urgency override authority. |
| Dispatcher | Lease authorized work to an eligible Executor. | Dispatch beyond current scope or capability. |
| Execution Monitor | Track leases, evidence, deadlines, retries, and stop conditions. | Conceal failure or approve completion. |
| Synchronizer | Reconcile Runtime and authoritative sources with explicit precedence. | Silently overwrite contradiction or history. |
| Checkpoint Manager | Capture context-complete state at meaningful boundaries. | Certify state beyond supplied evidence. |
| Telemetry and Health | Report reliability, throughput, and governance-compliance signals. | Turn metrics into policy or capture sensitive payloads. |
| Notifier and Escalation Router | Route actionable information and decision requests. | Interpret silence or delivery as approval. |

### 9.2 Event and work invariants

A Runtime event preserves a stable ID, type and schema version, source identity
and timestamps, actor and subject when known, correlation and causation IDs,
payload digest and reference, epistemic classification, sensitivity, trust
level, idempotency key, provenance, and ontology relationships. Events are
immutable observations; correction is a linked new event.

A work item preserves objective, source event, scope, allowed and prohibited
actions and resources, outputs, acceptance criteria, Verification plan,
authority requirements and current artifact, risk, priority rationale,
dependencies, deadlines and review triggers, eligible capabilities, retry
policy, stop conditions, state history, evidence, and learning references.
A work item is never itself authorization.

### 9.3 State and transition model

The normal flow is:

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
`CANCELLED`, `FAILED`, and `SUPERSEDED`. No Executor can move its own work to
`VERIFIED_PASS` or `READY_FOR_PROMOTION`. Silence, timeout, schedule, and
inferred intent cannot authorize promotion. `UNKNOWN` and
`MORE_EVIDENCE_REQUIRED` are honest gate outcomes.

### 9.4 Reliability and safe degradation

Runtime assumes at-least-once delivery and uses stable idempotency keys.
Execution authority is carried by expiring leases. Retries are bounded by
attempt, time, cost, and risk; each retry is a new linked attempt, and an
irreversible retry requires fresh authorization.

Invalid identity, schema, repository, provenance, authority, or destructive
action is quarantined. Secret-bearing input is isolated rather than propagated.
If Memory, Knowledge, Verification, Governance, or Assurance is unavailable,
Runtime may continue only pre-authorized reversible observation and recording.
Promotion and irreversible action stop.

Runtime health states are `HEALTHY`, `DEGRADED`, `BLOCKED`, `UNSAFE`, and
`UNKNOWN`. Running processes alone never establish `HEALTHY`.

## 10. Memory architecture

| Layer | Purpose | Canonical boundary |
|---|---|---|
| Working memory | Ephemeral context for current execution. | Conversation and scratch state are never the durable source of truth. |
| Project memory | Durable context for an issue, PR, release, or subsystem. | Decisions first become reviewable here. |
| Institutional memory | Validated reusable knowledge across workstreams. | Promotion requires evidence and relationships, not polished prose. |
| Evolution memory | Historical continuity of beliefs, decisions, and authority. | Before-and-after state, disturbing evidence, and reopening conditions are preserved. |

The durable unit of learning is:

```text
prior model → disturbing evidence → revised model → tested consequence
```

The minimum fitting record type is used: Failure Record (FR), Rumination (RM),
Idea Evolution Record (IER), Reasoning Ledger (RL), Traceable Epistemic
Transition capsule (TET), Decision Record, Pattern, anti-pattern, Risk,
Assumption, Experiment, or Unexpected Success Record. Existing governance and
architecture Decision Record namespaces are not duplicated.

Memory capture is triggered by material failure, changed belief, contradiction,
repeated investigation, unexpected success, architecture decision, release or
rollback, governance exception, prevented recurrence, or correction of inherited
knowledge. Memory records; Verification validates claims; Knowledge evaluates
relationships and gravity; Governance authorizes higher-layer change.

## 11. Knowledge and learning flow

The canonical handoffs are:

1. Intent gives Planning an objective, constraints, authority source, and
   acceptance criteria.
2. Planning gives Governance a proposed plan, risks, irreversible actions, and
   requested Delegations.
3. Governance gives Orchestration and Runtime bounded authorization, gates,
   expiry, and stop conditions.
4. Execution gives Verification artifacts, criteria, evidence, and provenance.
5. Verification gives Assurance results, unknowns, contradictions, and scope.
6. Assurance gives Governance a readiness result, never authority.
7. Every engine gives Memory context-complete events and decisions.
8. Memory gives Knowledge validated, provenance-preserving records.
9. Knowledge gives Evolution patterns, contradictions, gravity changes, and
   Genome gaps.
10. Evolution gives Governance proposals only.

This flow is cyclic for learning but acyclic for authority. No learning loop may
grant itself permission or silently mutate its governing layer.

## 12. Governance, Verification, and Assurance

For a Material Action:

1. the responsible Principal establishes intent and acceptance conditions;
2. Governance resolves a valid Delegation and exact Boundary;
3. an Executor acts only within that Boundary;
4. independent Verification evaluates evidence against unchanged conditions;
5. Assurance evaluates readiness where required;
6. the responsible Principal or properly delegated authority accepts, rejects,
   resumes, corrects, abandons, or terminates the work.

An Executor's report may be evidence but cannot establish its own Verification.
An Assurance result cannot authorize action. A Governance decision cannot
manufacture evidence. Runtime cannot infer approval. Acceptance remains a
Principal right unless explicitly delegated within constitutional limits.

When authority is insufficient or ambiguous, the Executor Halts under
[A-0001](../governance/constitution/Amendment-A-0001.md) because continuation
would exceed or risk exceeding its Boundary. Halt authority does not confer
authority to correct, resume, accept, abandon, or terminate.

## 13. Safety and security invariants

- Least authority: absence of prohibition is not Delegation.
- Human authority: irreversible actions require explicit, current authority.
- Revocability: Delegations and leases can be narrowed, revoked, or expired.
- Separation: no delegated Material Action places execution, Verification, and
  acceptance under one actor.
- Evidence integrity: original evidence, failures, corrections, and
  contradictions remain inspectable.
- Honest state: unknown, conflict, stale, and not-ready are never presented as
  success.
- Identity and scope: repository, actor, Principal, and target are verified
  before dispatch.
- Secrets: Runtime coordinates references and permissions; it does not expose
  or preserve secret values in events, telemetry, or memory.
- Failure containment: bounded retries, quarantine, Halt, and safe degradation
  take precedence over continuation.
- No emergency expansion: emergency action is limited to Halt, evidence
  preservation, prevention of immediate Material harm, and safe state.

## 14. TARP-0001 traceability

TARP-0001 applies to decisions materially affecting boundaries, authority,
persistence, security, reliability, release behavior, shared standards,
canonical workflows, memory, Foundational Concepts, principles, Patterns, or
difficult-to-reverse choices.

Each review packet states the decision, context, evidence, assumptions,
alternatives, constitutional and Foundational Concept alignment, principle and
Pattern alignment, implementation mapping, consequences, Verification plan,
reopening conditions, and durable links.

Review proceeds in this order:

1. constitutional compatibility;
2. Foundational Concept compatibility;
3. Architectural Principle compatibility;
4. Pattern compatibility;
5. implementation fidelity;
6. Verification and learning.

The durable chain is:

```text
Constitutional basis
  → Foundational Concept alignment
  → Ontology
  → Architectural Principle / candidate
  → Contract / Pattern
  → Decision or ADR
  → Issue
  → PR or diff
  → Verification evidence
  → Assurance and Governance decision
  → Release
  → Memory and learning record
```

Required outcomes are `APPROVED`, `APPROVED WITH CONDITIONS`, `REVISE`,
`REJECTED`, `DEFERRED`, or `SUPERSESSION REQUIRED`. A future reviewer must be
able to reconstruct what was decided, why, under which authority, from which
evidence, how it was realized and verified, and what would reopen it without
private conversation.

## 15. Candidate and Genome lifecycle

Every candidate record includes stable identity, definition, scope, non-goals,
constitutional and Foundational Concept alignment, supporting and contradicting
evidence, independent and failed applications, reuse, gravity and Genome state,
target layer, links, review date, and reopening conditions.

The canonical detailed candidate lifecycle is:

```text
PROPOSED → OBSERVED → VALIDATING → QUALIFIED
  → PROMOTION_REVIEW → ADOPTED → SUPERSEDED | RETIRED
```

`REJECTED`, `DEFERRED`, `NEEDS_EVIDENCE`, and `WITHDRAWN` preserve non-adoption
paths. No candidate advances from conversational support alone.

Promotion to Foundational Concept requires:

1. successful application across at least three independent architecture
   workstreams;
2. no unresolved constitutional conflict;
3. a positive TARP-0001 review;
4. demonstrated improvement in clarity, governance, or engineering quality; and
5. explicit Governance approval under valid authority.

Engineering Genome membership follows:

```text
PROPOSED → OBSERVED → VALIDATED → INCORPORATED → CHARACTERISTIC
  → FOUNDATIONAL (when applicable) → SUPERSEDED | RETIRED
```

Recurring evidence across projects or subsystems is required. Every adoption,
promotion, removal, or retirement preserves evidence, rationale, TARP
traceability, and a reversal path.

## 16. Implementation roadmap

This sequence is a planning dependency, not implementation authorization:

1. **Canonical specification:** review and adopt this architecture through
   Issue #19.
2. **Implementation blueprint:** use
   [Issue #21](https://github.com/AgentiCubed/agenticubed/issues/21) to map every
   contract to owned modules, logical APIs, persistence interfaces, tests,
   deployment boundaries, milestones, rollback, and release gates.
3. **Ontology foundation:** establish stable IDs, versions, typed relationships,
   provenance, and explainable query contracts before automating promotion.
4. **Authority and evidence slice:** implement the smallest independently
   testable Governance, Verification, and Assurance path for one reversible
   workflow.
5. **Memory and Knowledge slice:** preserve checkpoints and one end-to-end
   learning transition; keep gravity and Genome decisions human-reviewed.
6. **Runtime slice:** add idempotent observation, queueing, expiring leases,
   bounded retries, Halt, quarantine, and recovery for reversible work.
7. **Evolution and candidate review:** schedule revalidation and produce change
   proposals without automatic higher-layer mutation.
8. **Hardening:** validate identity, multi-scope authorization, source
   precedence, retention, clock behavior, failure recovery, alerting, and
   operational cost before expanding autonomy.

Each slice must be independently releasable, preserve historical continuity,
and stop at the first unavailable authority, Verification, or Assurance gate.
Database, queue, workflow, cloud, and model vendors remain blueprint and ADR
decisions rather than constitutional architecture.

## 17. Unresolved risks

- Relationship vocabulary and metadata may become too broad or costly to curate.
- Engine ownership may become ambiguous for composite artifacts.
- Knowledge Gravity may degrade into false precision or popularity scoring.
- Genome membership may become difficult to reverse in practice.
- Semantic contradiction detection may overstate conflict without scope and
  temporal context.
- Legacy records may be incomplete for historical reconstruction.
- Ontology evolution may require compatibility mappings and migrations.
- Source-of-truth precedence across repositories, CI, Runtime, and memory needs
  an explicit policy.
- Event volume, retention cost, delayed delivery, and clock skew are unknown.
- Multi-scope identity and authorization semantics need implementation evidence.
- Physical consolidation of engines may erode logical independence.
- Notifications may create alert fatigue or be mistaken for acknowledged
  authority.
- Continuous coordination may cost more than the value of the work it schedules.
- A vendor-specific implementation may accidentally harden into policy.

These are active design risks, not implied defects in a selected implementation.

## 18. Reopening conditions

Reopen this specification when any of the following occurs:

- constitutional amendment or authorized interpretation changes an applicable
  authority boundary;
- a Foundational Concept is superseded or a candidate is promoted;
- two engines require conflicting write or decision authority;
- a material engineering question cannot be expressed by the ontology;
- relationship capture costs exceed demonstrated retrieval and assurance value;
- graph integrity rules block legitimate historical or epistemic representation;
- query explanations are insufficient for independent review;
- gravity becomes opaque scoring or Genome membership becomes irreversible;
- implementation cannot preserve engine separation, historical continuity,
  idempotency, or safe degradation;
- Runtime state is ambiguous, unrecoverable, or enables unsafe autonomy;
- a simpler architecture demonstrates equal traceability and safety at lower
  coordination cost;
- this specification conflicts with the reviewed implementation blueprint or
  repeated implementation evidence.

Revision must preserve the prior version, evidence that triggered reopening,
the authorized decision, compatibility impact, and migration or supersession
path.

## 19. Acceptance tests for this architecture

The architecture is context-complete only if a reviewer can answer:

- Who authorized a Material Action, under what Boundary, and until when?
- Which engine planned, executed, verified, assured, governed, and accepted it?
- Which constitutional and Foundational Concepts constrain an implementation?
- Which evidence supports a claim and what remains unknown or contradictory?
- What failure, success, or experiment produced a lesson?
- Why did knowledge gain or lose gravity?
- Which Genome version contained a member and how can it be reversed?
- What is affected when a principle, contract, or entity is superseded?
- Which candidates remain unpromoted and what evidence would qualify them?
- Can the complete decision be reconstructed from durable links without
  conversational memory?

If any answer requires hidden context, inferred authority, or an opaque model
result, the relevant architecture record is incomplete.
=======
# Agentic³ Unified Architecture Specification v2 — DRAFT (partially filled)

> **Status: draft, unblocked sections filled.** This document is the
> consolidation target for issue #19. Sections §1, §2, §5.1–§5.4, §5.6, §7,
> and §9 are drafted from ratified and adopted sources; sections marked
> **[BLOCKED: #16]** or **[BLOCKED: #17]** cannot be finalized until those
> design workstreams conclude, and their headings are fixed so the
> consolidation has a stable shape. Everything here is design and
> specification — no product code, no database or vendor selection, no
> candidate promotion without evidence, no Constitution v1.0 rewrite
> (issue #19 non-goals).

## 0. Reading this document

This specification must be interpretable without conversational memory
(issue #19 acceptance criterion). Every referenced authority is either linked
to a repository artifact or listed in §0.1 as **not yet landed** — a reader
finding a dangling name should treat that as a defect in this document, not as
missing context they were supposed to have.

### 0.1 Input register

| Input | Repository artifact | State |
|-------|--------------------|-------|
| Constitution v1.0 | [`../governance/constitution/Constitution-v1.0.md`](../governance/constitution/Constitution-v1.0.md) | Ratified ([RR-0001](../governance/ratification/RR-0001.md)) |
| Amendment A-0001 (halt on insufficient/ambiguous authority) | [`../governance/constitution/Amendment-A-0001.md`](../governance/constitution/Amendment-A-0001.md) | Ratified |
| Amendment procedure | [`../governance/decisions/DR-0001-Constitutional-Amendment-Procedure.md`](../governance/decisions/DR-0001-Constitutional-Amendment-Procedure.md) | Adopted |
| Institutional memory system (issue #12) | [`../governance/knowledge/`](../governance/knowledge/) (README, record types, templates, transmission) | Landed; issue closed complete |
| AC-0001 Knowledge Gravity | [`concepts/AC-0001-knowledge-gravity.md`](concepts/AC-0001-knowledge-gravity.md) | Proposed — landed as a reconstruction from issue-text usage; Principal adoption decision pending (§7 state 1) |
| AC-0002 Engineering Genome | [`concepts/AC-0002-engineering-genome.md`](concepts/AC-0002-engineering-genome.md) | Proposed — same condition as AC-0001 |
| AC-0003 Architectural Contracts | **none** | Candidate — must land with candidate status explicit |
| AC-0004 Separation of Decision and Execution | **none** | Candidate — note: the *shipped platform* already enforces executor/evaluator separation (ADR-0004); the candidate generalizes it |
| AC-0005 Explicit Relationships | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| AC-0006 Semantic Inheritance | **none** | Candidate — adopt/modify/reject decision owned by #16 |
| TARP-0001 traceability | [`TARP-0001-traceability-protocol.md`](TARP-0001-traceability-protocol.md) | Proposed — chain and review rules landed; acronym expansion and the still-unlanded **Upward Compatibility Rule** flagged inside |
| Ontology & semantic graph | issue #16 (open) | **[BLOCKED: #16]** |
| Runtime Domain & continuous operation | issue #17 (open) | **[BLOCKED: #17]** |

### 0.2 Relationship to the shipped platform

The AgentiCubed platform (backend/, frontend/ — see
[`../architecture.md`](../architecture.md)) is a working implementation whose
seams (ports/adapters, executor–evaluator separation, append-only audit, the
new live event stream) are *evidence* for several candidate principles. This
specification governs the architecture of Agentic³ as a system-of-record and
engineering institution; it does not retro-specify the platform, and the
platform does not automatically instantiate this spec.

## 1. Mission

Agentic³ exists to coordinate human and autonomous contributors through
planned, reviewable, evidence-backed work (Constitution, Preamble). Its
architecture answers one question: how does an engineering institution stay
trustworthy when the capability and diversity of its contributors — human and
AI — grow faster than any individual's ability to supervise them?

The answer the Constitution commits to is structural, not supervisory.
Authority, verification, accountability, and institutional continuity must not
depend on individual judgment or temporary context (Preamble). Instead:

- **Authority is explicit and revocable.** All authority originates with a
  Principal and reaches Executors and Evaluators only through Delegation with
  a defined Boundary (Art. III). Nothing in the system may obstruct
  revocation (Art. IV §3).
- **Claims require evidence.** A claim about a Material Action must be
  supported by inspectable Evidence proportionate to its consequences
  (Art. VI §1), and no Executor may be the sole source of evidence for its
  own success (Art. VI §3).
- **Work that cannot proceed legitimately halts.** When authority is
  insufficient or ambiguous, the required behavior is Halt — never inference
  of broader authority (Art. VII §4, as clarified by Amendment A-0001).
- **The institution remembers.** Failures, reasoning, and idea evolution are
  preserved as context-complete records (§5.1–§5.2) so future contributors
  reuse the search path, not just its conclusion.

Two boundaries keep the mission honest. First, governance exists to improve
the product; the product does not exist to justify governance (Preamble).
Second, the Constitution governs only enduring matters — authority, rights,
evidence, autonomy, precedence, emergency, supremacy, amendment (Art. I §1) —
and everything else, including this specification's subordinate details, must
remain revisable without constitutional change (Art. I §2).

## 2. Authority hierarchy

### 2.1 Roles (Art. II)

Three roles exhaust the authority model. A **Principal** holds ultimate
authority and accountability within a defined scope. An **Executor** performs
work under Delegation. An **Evaluator** determines whether work satisfies
established conditions. Roles are positional, not personal: the same entity
may be Principal in one scope and Executor in another, but never Executor and
sole Evaluator of the same Material Action (Art. V §3).

For current repository work, POL-0001 names the concrete binding: James
Richmond is the Principal for AgentiCubed engineering; delegated agents act as
Executors within gate Boundaries. This binding is a subordinate-instrument
fact and may change without touching this section's model.

### 2.2 Sovereignty and delegation (Art. III)

Every Delegation names its originating Principal, its receiving Executor or
Evaluator, and its Boundary (Art. III §1). Three structural consequences
follow:

1. **No authority is created downstream.** A Principal delegates only what it
   possesses; Delegation cannot enlarge itself; sub-delegation exists only
   when expressly permitted (Art. III §2).
2. **Accountability does not transfer.** The responsible Principal remains
   ultimately accountable for delegated work, while the Executor or Evaluator
   remains responsible for its own actions within the grant (Art. III §3).
3. **Revocation always works.** No Delegation may prevent its own revocation,
   and revocation never erases Evidence or the historical record
   (Art. III §4).

### 2.3 Rights of Principals (Art. IV)

The Principal's rights form the fixed points every engine in §5 must respect:
intent (no Executor or Evaluator may redefine it), evidence (nothing Material
may be withheld; every Material Action must remain traceable to its
Delegation), revocation (unobstructable), and ownership (artifacts, Evidence,
and governance records belong to the Principal absent explicit transfer).
No subordinate instrument — including this specification — may diminish these
rights (Art. IV §5).

### 2.4 Separation of authority (Art. V)

Where any part of a Material Action is delegated, no single Executor or
Evaluator controls execution, verification, *and* acceptance (Art. V §1). An
Executor's account of its own work is Evidence but never Verification
(Art. V §3), and Delegations must preserve enough independence for
Verification to genuinely challenge the Executor (Art. V §4 — the mechanism
lives outside the Constitution, and outside this section).

Relation to candidate **AC-0004 (Separation of Decision and Execution)**: the
constitutional rule separates execution from verification/acceptance of the
*same action*; the candidate proposes a broader separation between deciding
and doing. They are related but not identical, and the shipped platform's
executor/evaluator enforcement (ADR-0004) is evidence for the constitutional
rule — not for the candidate, which remains unlanded and unevaluated (§0.1).

### 2.5 Halt semantics (Art. VII §4, Art. IX, Art. X, A-0001)

The halt model has three tiers:

- **Principal halts** are unrestricted within the Principal's authority
  (Art. IX §1).
- **Executor/Evaluator halts** are restricted to the exhaustive Art. IX §2
  grounds (boundary exceedance, evidence corruption or concealment,
  unauthorized Material Action, constitutional violation, fault propagation).
  Amendment A-0001 closes the seam between this list and Art. VII §4: a halt
  for insufficient or ambiguous authority *is* an Art. IX halt, grounded in
  actual or threatened Boundary exceedance.
- **Emergency actions** (Art. X) activate only narrow protective authority —
  preserve a halt, preserve evidence, prevent immediate Material harm, reach
  a safe condition — and never completion, verification, expansion,
  concealment, or amendment.

Initiating a halt confers no authority over what happens next; correction,
resumption, acceptance, abandonment, and termination each require authority
independently established under Art. III (Art. IX §3). Non-convergence never
justifies indefinite execution or fabricated success (Art. IX §5).

## 3. Ontology **[BLOCKED: #16]**

*The canonical entity taxonomy, controlled relationship vocabulary, identity/
versioning/provenance semantics, lifecycle states, graph integrity rules, and
query semantics shared by every engine.*

Fixed subsection shape (mirrors issue #16 required outputs):

- 3.1 Root entity model
- 3.2 Entity families (actor, system, knowledge, artifact, evidence,
  governance, temporal)
- 3.3 Relationship vocabulary (source/target constraints)
- 3.4 Identity, versioning, provenance, authority semantics
- 3.5 Lifecycle states and transition constraints
- 3.6 Graph integrity rules
- 3.7 Knowledge Gravity metadata and update rules *(AC-0001 landed as a
  proposal; also awaiting its adoption decision)*
- 3.8 Engineering Genome membership and evolution *(AC-0002 landed as a
  proposal; also awaiting its adoption decision)*
- 3.9 Query semantics (provenance, impact, contradiction, authority, reuse)
- 3.10 AC-0005 / AC-0006 adopt–modify–reject decisions

## 4. Domains

*The domain map: Executive Domain (approved), Runtime Domain (#17), and any
domains the #16/#17 outcomes introduce. Each domain states its authority
boundary and its constitutional basis.*

- 4.1 Executive Domain **[DRAFT — cite the approving artifact; if approval
  exists only conversationally, it must land first (same rule as §0.1)]**
- 4.2 Runtime Domain **[BLOCKED: #17]** — observe, schedule, queue,
  synchronize, learn, report continuously without an active chat session,
  preserving human authority over irreversible actions
- 4.3 Domain interaction contracts **[BLOCKED: #16 relationships, #17]**

## 5. Engines

An **engine** is a named institutional capability with a bounded
responsibility, defined inputs and outputs, and explicit authority limits.
Engines are roles the institution performs, not services or processes — how
each is realized (by people, agents, tooling, or the platform) is an
implementation choice outside this specification. The definitions below are
deliberately non-overlapping (issue #19 acceptance criterion); §5.5 remains
open, and its eventual definition may narrow — never contradict — the others.

Every engine operates under §2: engines hold no authority of their own, only
authority reaching them through Delegation.

### 5.1 Memory engine

**Purpose:** preserve institutional state across time and contributors, in
four bounded stores (issue #12): *working memory* (the live context of an
active effort — legitimate but disposable), *project memory* (the durable
record of one project), *institutional memory* (cross-project records:
failures, reasoning, patterns), and *evolution memory* (how beliefs and
designs changed, and why).

**Inputs:** capture triggers defined by the knowledge system (failures,
decisions, belief changes, unexpected successes). **Outputs:** durable,
append-only records with stable identifiers. **Authority limits:** memory
records confer no authority (§0.1's rule generalized: existence of a document
is never authority — Art. XI gives that role to the Constitution and
instruments traceable to a Principal). Corrections preserve the prior
statement, the correction, the evidence, and the date; historical claims are
never erased (knowledge README, Maintenance).

**Governing thesis** (issue #12): the durable unit of learning is not a
conclusion but the traceable transition
`prior model → disturbing evidence → revised model → tested consequence`.

### 5.2 Knowledge engine

**Purpose:** turn preserved memory into reusable engineering knowledge by
enforcing the record taxonomy and its quality rules.

**Record taxonomy** (per
[`../governance/knowledge/README.md`](../governance/knowledge/README.md)):
Failure Record (FR — observed vs. expected behavior, evidence, impact,
correction, verification, unresolved facts; no blame, no motive speculation),
Rumination (RM — hypothesis-level analysis linked to an FR, with rejected
explanations and updated mental models), Idea Evolution Record (IER — the
chronology of an idea including discarded branches and reopening conditions),
and Reasoning Ledger (RL — claim, assumptions, evidence, counter-evidence,
alternatives, confidence before/after, the trigger that changed confidence,
remaining uncertainty). Records cross-link by stable identifier
(`FR-NNNN`, `RM-NNNN`, `IER-NNNN`, `RL-NNNN`).

**Quality rules the engine enforces:**

- *Context-complete review*: a record fails review if a future contributor
  must ask what happened, where, on what evidence, which statements are fact
  versus interpretation, or what changed as a result.
- *Fact/interpretation separation*: interpretation must remain visibly
  distinct from verified fact — the epistemics that Art. VI §5 (honest state)
  demands of claims, applied to records.
- *Transmission discipline*: retelling knowledge adds value only when it
  improves discoverability, context, validation, applicability, correction,
  connection, or resilience; otherwise transmission degrades it.

**Authority limits:** knowledge records inform decisions; they never make
them. A Pattern is not a policy.

### 5.3 Governance engine

**Purpose:** maintain the instruments through which authority flows — the
Constitution and its amendments, ratification records, and the subordinate
policy/procedure/standard layer — and operate the gate workflow that turns
authority into authorized work.

**Constitutional layer:** amendments follow Art. XII — complete proposal
(deficiency, change, affected authority, why no subordinate instrument
suffices, interpretive effect), independent context-complete review by a
non-drafter, explicit Principal ratification, durable historical continuity.
DR-0001 operationalizes this procedure; RR-0001 is the ratification record of
the v1.0 baseline.

**Subordinate layer:** policies (POL), procedures (PROC), standards (STD),
and templates (TPL) govern what the Constitution deliberately leaves open
(Art. I §2). They hold authority only while consistent with the Constitution
(Art. XI) and traceable to a Principal (Art. VIII §4).

**Operating model:** the gate workflow (POL-0001). The Principal defines each
gate (objective, scope, acceptance conditions, boundary, expected evidence,
stop conditions); the Executor acts within it and returns complete evidence;
the Principal reviews and decides — next gate, correction gate, or halt. No
work begins without authorization; silence is never authority.

**Authority limits:** the governance engine administers instruments; it never
ratifies. Ratification and gate authorization belong to Principals alone
(Art. XII §3, POL-0001).

### 5.4 Verification engine

**Purpose:** evaluate Evidence against established conditions (Art. II) and
maintain the institution's honest state.

**Duties, all from Art. VI:** demand evidence proportionate to consequences
(§1); keep evidence inspectable by those authorized to review it (§2); refuse
sole self-attestation — no Executor is the only source of evidence for its
own success (§3); insist acceptance conditions exist *before* execution and
that only the responsible Principal changes them, with the change preserved
as evidence (§4); never represent unverified work as verified (§5); preserve
evidence long enough for verification, accountability, and authorized review
(§6).

**Structural position:** verification is independent by construction
(Art. V §4) and cannot be collapsed into execution (Art. V §1, §3).

**Relation to the platform:** the shipped evaluation subsystem — deterministic
rubrics, evaluator agents, enforced executor/evaluator separation (ADR-0004)
— is an *implementation instance* and supporting evidence for this engine's
feasibility. It is not the engine's definition, and platform behavior never
substitutes for constitutional duty (§0.2).

**Authority limits:** verification determines whether conditions are
satisfied; acceptance remains the Principal's (Art. IV §1, Art. IX §3).

### 5.5 Assurance engine **[BLOCKED: #17]**

*Continuous-operation assurance: how the institution stays confident in an
always-on system between explicit verification events. Boundary with §5.4 to
be drawn on #17 closure (risk R3).*

### 5.6 Evolution engine

**Purpose:** change the institution's own architecture safely — owner of the
candidate lifecycle (§7) and steward of evolution memory (§5.1).

**Inputs:** candidate principles (AC-XXXX), evidence from repeated
application, contradictions surfaced by the knowledge engine, and reopening
conditions attached to prior decisions. **Outputs:** adopt / modify / reject
decisions with their reasoning preserved (RL), updates to the traceability
chain (§8), and amendments proposed — never enacted — when a deficiency is
genuinely constitutional (Art. XII §1).

**Authority limits:** the evolution engine evaluates and recommends;
adoption is a governance act requiring authority traceable to a Principal
(§7). It may not promote a candidate by accumulation of citations, habit, or
document age — the failure mode issue #16 names "scoring theater" and R1/R2
track.

## 6. Runtime **[BLOCKED: #17]**

*Continuous operation model: schedulers, queues, synchronization, learning
loops, reporting; what may run unattended; what always requires a Principal.
Constitutional constraints: Bounded Autonomy (Art. VII), Halt/Escalation
(Art. IX incl. A-0001), Emergency (Art. X).*

## 7. Candidate lifecycle

An **Architectural Candidate (AC-XXXX)** is a proposed enduring principle of
Agentic³ architecture. Candidates exist so the institution can *try* a
principle repeatedly before committing to it — the opposite of ratifying
ideas at the moment of enthusiasm.

**Lifecycle states:**

1. **Proposed.** The candidate lands as a repository artifact stating: the
   principle, the problem it addresses, its predicted consequences, what
   evidence would support or refute it, and its reopening conditions. Until
   the artifact lands, the candidate does not exist for governance purposes
   (§0.1) — issue text is a proposal to propose.
2. **Under evaluation.** The candidate is applied where it naturally fits and
   each application is recorded with outcome evidence (RL entries linking to
   the candidate). Evaluation is repeated: a single success or failure is an
   anecdote, not a verdict (issue #16 acceptance criterion: decisions "only
   after repeated evaluation").
3. **Decided.** The evolution engine (§5.6) synthesizes the evidence and
   recommends **adopt**, **modify** (returning to state 1 as a revised
   proposal), or **reject**. The decision itself is a governance act under
   authority traceable to a Principal (§5.3), preserved with its full
   reasoning ledger.
4. **Adopted / Rejected — both with reopening conditions.** Adoption adds the
   principle to the traceability chain (§8) and, where issue #16's terms
   apply, to Engineering Genome membership — which is "explicit, versioned,
   and reversible." Rejection preserves the candidate, its evidence, and what
   would justify revisiting it. Neither state erases history (Art. XII §4 by
   analogy; knowledge README, Maintenance).

**Hard rules:**

- Authority is conferred through governance relationships, never through
  document existence, citation frequency, or age (issue #16).
- Shipped code that resembles a candidate is evidence of feasibility, not
  adoption (§0.2, risk R2).
- No candidate becomes constitutional by adoption; if a candidate's substance
  belongs in the Constitution, that is an Art. XII amendment with its own
  procedure.

**Proposed governance decision GD-P1 — applicability to Foundational
Concepts.** This section was written for Architectural Candidates (chain
layer 4). Whether the same lifecycle formally governs **Foundational
Concepts** (chain layer 2 — AC-0001, AC-0002) has never been decided; the
landed concept proposals *assume* it does, and flag that assumption. The
proposal: **the §7 lifecycle governs layer-2 Foundational Concepts and
Engineering Genome membership exactly as it governs layer-4 candidates.**
Alternatives the Principal may prefer: a stricter procedure for layer 2
(closer to Art. XII amendment discipline, since concepts sit directly under
the Constitution), or a distinct lightweight track. Until decided, no
lifecycle claim about a Foundational Concept is enforceable. Decision owner:
the Principal (Art. III).

**Current registry:** AC-0001 and AC-0002 have landed as proposals (state 1;
see §0.1) with every rule labeled supported/reconstructed/proposed;
AC-0003…AC-0006 remain named candidates awaiting artifacts and cannot enter
state 2 until state 1 is satisfied (§10 item 1).

## 8. Traceability

*The TARP-0001 chain: Constitution → Foundational Concepts → Ontology →
Architectural Principles → Patterns → Implementations. Every durable
architectural statement must be traceable along explicit relationships
(issue #16 acceptance criterion).*

**[PARTIALLY UNBLOCKED: TARP-0001 landed as a proposed protocol
([`TARP-0001-traceability-protocol.md`](TARP-0001-traceability-protocol.md))
defining the chain and review rules. This section finalizes after (a) the
Principal's adoption decision on that proposal and (b) issue #16 fixes the
relationship semantics a "trace" is made of.]**

## 9. Safety

Agentic³'s safety posture is *structural*: it does not depend on any
contributor — human or AI — choosing well under pressure, because the
architecture removes the authority to choose badly.

**The five load-bearing properties:**

1. **Human authority over what matters.** Every Material Action traces to a
   Delegation from a Principal (Art. III, Art. VII §3); intent belongs to the
   Principal alone (Art. IV §1); revocation is unobstructable (Art. IV §3).
   Autonomy is real but bounded — execution without contemporaneous direction
   is valid *only inside* an existing Delegation (Art. VII §1).
2. **Halt-first defaults.** Insufficient or ambiguous authority means halt,
   never inference (Art. VII §4, A-0001). Objectives, deadlines, and progress
   expectations authorize nothing beyond the Boundary (Art. VII §5), and
   repeated failure never justifies indefinite execution or fabricated
   success (Art. IX §5). Halting is the required behavior, not a failure mode
   (POL-0001).
3. **Evidence before belief.** Claims require proportionate, inspectable
   evidence (Art. VI §1–2); no executor self-attests alone (Art. VI §3);
   unverified work is never represented as verified (Art. VI §5). Acceptance
   conditions predate execution (Art. VI §4), which forecloses success-
   criteria drift after the fact.
4. **No self-expansion, no laundering.** An Executor cannot expand its own
   authority or create a Delegation for itself (Art. VII §2) — and authority
   obtained *through another Executor* stays subject to the original
   Boundary, closing the confused-deputy path. Absence of prohibition is not
   Delegation (Art. VII §5).
5. **Emergencies stay narrow.** Emergency authority covers only halting,
   evidence preservation, harm prevention, and safe states (Art. X §2); it
   can never complete, verify, expand, conceal, or amend (Art. X §3), and it
   expires rather than normalizes (Art. X §5).

**Precedence under conflict:** when interests collide, protection beats
continuation (Art. VIII §2) and ambiguity resolves toward *less* authority
(Art. VIII §3). The full order — Constitution, Principal rights, Principal
decisions, Delegation/Boundary, acceptance conditions, and only then
continuation or efficiency — is Art. VIII §1.

**Implementation evidence (not definition):** the shipped platform exhibits
these properties concretely — RBAC and default-deny tool permissions, agents
barred from changing their own permissions, human approval gates before
irreversible actions, append-only audit/execution/evaluation records, and
secrets referenced by key rather than value
([`../security-model.md`](../security-model.md)). Per §0.2, this is evidence
the posture is buildable, not the posture itself.

## 10. Roadmap

*Sequencing to v2-final:*

1. Land the missing foundational artifacts — **partially done**: AC-0001,
   AC-0002, and TARP-0001 landed as proposals (adoption decisions pending);
   candidate texts AC-0003…AC-0006 and the Upward Compatibility Rule still
   unlanded
2. Close issue #16 (ontology) — unblocks §3, §4.3
3. Close issue #17 (Runtime Domain) — unblocks §4.2, §5.5, §6
4. ~~Fill §1, §2, §5.1–5.4, §5.6, §7, §9~~ — **done** (this revision)
5. Consolidation review under STD-0001 (context-complete review), then
   ratify per the gate workflow (POL-0001)

## 11. Open risks and reopening conditions

- **R1 — Reconstruction risk (updated):** Knowledge Gravity, Engineering
  Genome, and TARP-0001 now exist as landed *reconstructions* from issue-text
  usage, awaiting Principal adoption decisions. The original drift risk is
  narrowed but not closed: the reconstructions may not match the Principal's
  intent, and issue #17 already treats AC-0001/0002 as "approved" without a
  recorded decision. *Reopen §3/§7/§8 if the adoption review corrects the
  reconstructions; resolve the approval-status discrepancy at that review.*
- **R2 — Platform/spec conflation:** the shipped platform's seams look like
  the candidate principles; treating shipped code as proof of adoption would
  promote candidates without governance. *Reopen §0.2 if any engine section
  starts citing code as authority.*
- **R3 — Engine overlap:** Verification vs. Assurance boundaries are
  undefined until #17 lands. *Reopen §5 on #17 closure.*
- **R4 — Amendment interactions:** future amendments (post A-0001) may alter
  halt semantics assumed in §6/§9. *Reopen on any Article VII/IX/X amendment.*
>>>>>>> origin/main
