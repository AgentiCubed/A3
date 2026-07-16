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
| AC-0004 | Separation of Decision and Execution | Proposed Foundational Candidate | Distinct planning, authorization, execution, Verification, Assurance, and acceptance boundaries prevent self-authorization and self-certification. |
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
Transition capsule (TET), Decision Record, Pattern, Anti-pattern, Risk,
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
