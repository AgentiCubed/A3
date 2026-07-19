# ONTO-0002 — Relationship Vocabulary

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Purpose

This document defines the complete controlled vocabulary of relationships between Agentic³
entities. Every semantic connection between entities must use one of these named relationships.
Implicit connections are not permitted (Upward Compatibility Rule: AC-0005 Explicit
Relationships is under evaluation; see ONTO-0006).

---

## 2. Relationship Schema

Every relationship record has:

| Field | Required | Description |
|---|---|---|
| `relationship_type` | Yes | One of the named types below. |
| `source` | Yes | The entity initiating or holding the relationship. |
| `target` | Yes | The entity receiving or completing the relationship. |
| `asserted_by` | Yes | The actor or system that asserted this relationship. |
| `asserted_at` | Yes | Timestamp when the relationship was asserted. |
| `authority` | Yes | Governance basis for the relationship's existence (delegation, decision, ratification). |
| `evidence_refs` | Conditional | Required for `EVIDENCES`, `CONTRADICTS`, `PROMOTES_TO`, and `SUPERSEDES`. |
| `notes` | Optional | Human-readable annotation; not a substitute for a knowledge record. |

Relationships are append-only once asserted. A relationship is retracted by adding a
`SUPERSEDES` relationship (or a type-specific revocation relationship such as `REVOKES`), not by deletion.

---

## 3. Relationship Types

### 3.1 Authority and Governance Relationships

These relationships establish who has authority over what and how decisions flow.

| Relationship | Source | Target | Cardinality | Description |
|---|---|---|---|---|
| `GOVERNS` | Constitution, PlaybookDocument, GovernanceDecision | any Entity | 1:N | A governing instrument directly constrains the target. |
| `DELEGATES_TO` | Principal | Executor, Evaluator, Agent | 1:N | A Principal grants delegated authority within a Boundary. |
| `BOUNDED_BY` | Executor, Evaluator, Agent | Boundary | N:1 | The executing entity operates within this Boundary. |
| `RATIFIED_BY` | GovernanceDecision, ConstitutionalAmendment | Principal | N:1 | The decision or amendment was ratified by this Principal. |
| `AUTHORIZES` | GovernanceDecision, Delegation, TaskPacket | Entity, action (MaterialAction) | 1:N | The governance artifact authorizes this entity or action. |
| `REVOKES` | Principal | Delegation | N:1 | A Principal revokes a previously granted Delegation. |
| `SUPERSEDES` | GovernanceDecision, PlaybookDocument, any Knowledge entity | GovernanceDecision, PlaybookDocument, any Knowledge entity | N:1 | A new version or decision supersedes the prior, which is preserved. |
| `AMENDS` | ConstitutionalAmendment | Constitution | N:1 | A ratified amendment changes specific Constitution articles. |

**Integrity constraints:**
- `DELEGATES_TO` must link to a `Boundary` entity via `BOUNDED_BY` from the receiving entity.
- `REVOKES` may only be asserted by the same Principal that asserted the original
  `DELEGATES_TO`.
- `SUPERSEDES` must include `evidence_refs` identifying what caused the supersession.
- A `GOVERNS` relationship does not by itself confer authority; it records which instrument
  applies.

---

### 3.2 Execution Relationships

These relationships describe how work is performed and by whom.

| Relationship | Source | Target | Cardinality | Description |
|---|---|---|---|---|
| `EXECUTES_UNDER` | Executor, Agent | Delegation | N:1 | The executor performs this work under a specific Delegation. |
| `ASSIGNED_TO` | Task (project entity) | Agent, HumanContributor | N:1 | The task is assigned to this actor for execution. |
| `PRODUCED` | Executor, Agent | Artifact | 1:N | The actor produced this artifact during execution. |
| `INITIATED` | Principal, Executor, Event | Event | 1:N | The actor or event triggered another event or state change. |
| `DISPATCHED_BY` | WorkflowEngine | Agent, Executor | 1:N | The engine dispatched work to this executor. |
| `RETRIED_AS` | TaskExecution | TaskExecution | 1:1 | This execution was retried as a new execution attempt. |
| `ESCALATED_TO` | Executor, Agent | Principal, HumanContributor | N:1 | The executor escalated a blocked or unresolvable situation to this actor. |

**Integrity constraints:**
- `EXECUTES_UNDER` must reference an active, non-revoked Delegation.
- `PRODUCED` artifacts must carry the execution's provenance in their own `provenance` field.
- `RETRIED_AS` is one-to-one: one execution produces at most one retry; the prior execution
  is not overwritten.

---

### 3.3 Evaluation and Verification Relationships

These relationships describe how work is assessed and verified.

| Relationship | Source | Target | Cardinality | Description |
|---|---|---|---|---|
| `EVALUATES` | Evaluator, Agent | Execution, Artifact | N:N | The evaluator assessed this execution or artifact. |
| `VERIFIED_BY` | Entity, MaterialAction | VerificationRecord | 1:1 | A Material Action or entity is verified by this record. |
| `EVIDENCES` | Evidence entity | Claim, Entity, VerificationRecord | N:N | The evidence supports or informs the target claim. |
| `CONTRADICTS` | Evidence entity, Knowledge entity | Claim, Knowledge entity | N:N | The source materially contradicts the target claim. Must include `evidence_refs`. |
| `REVIEWED_BY` | Artifact, GovernanceDecision, PlaybookDocument | ReviewRecord | 1:N | The artifact or document received a formal review. |
| `ACCEPTS` | Principal, ReviewRecord | TaskPacket, ReviewPacket | N:1 | The Principal accepted the work product against acceptance conditions. |
| `REJECTS` | Principal, ReviewRecord | TaskPacket, ReviewPacket | N:1 | The Principal rejected the work product. |

**Integrity constraints:**
- `EVALUATES` source and the `EXECUTES_UNDER` source of the evaluated work must be different
  entities (separation of executor and evaluator; Constitution Art. V §3).
- `VERIFIED_BY` requires that the `VerificationRecord` references at least one `Evidence` entity
  via `EVIDENCES`.
- `CONTRADICTS` must include `evidence_refs`; bare assertion of contradiction is not valid.
- `ACCEPTS` may only be asserted by the responsible Principal or their delegated Evaluator.

---

### 3.4 Knowledge and Traceability Relationships

These relationships describe how understanding was built, how decisions trace to higher authority,
and how knowledge evolves.

| Relationship | Source | Target | Cardinality | Description |
|---|---|---|---|---|
| `DERIVES_FROM` | ArchitecturalPrinciple, Pattern, Implementation | FoundationalConcept, ArchitecturalPrinciple | N:1 | The source concept is derived from the target higher-layer concept. |
| `IMPLEMENTS` | CodeArtifact, ServiceComponent, Configuration | ArchitectureDecisionRecord, ArchitecturalPrinciple, Pattern | N:N | The implementation realizes the target architectural intent. |
| `INFORMED_BY` | GovernanceDecision, ArchitectureDecisionRecord, ArchitecturalPrinciple | Evidence entity, Knowledge entity | N:N | The decision or principle was informed by this evidence or knowledge. |
| `LINKED_TO` | any Entity | any Entity | N:N | A generic navigable reference for related entities where no more specific relationship applies. Use sparingly. |
| `TRACES_TO` | Implementation | ConstitutionalArticle, FoundationalConcept, ArchitecturalPrinciple | N:N | Provides the full TARP-0001 traceability chain from implementation to higher authority. |
| `BASED_ON` | TETCapsule, IdeaEvolutionRecord | FailureRecord, ObservationRecord, ExperimentResult | N:N | The knowledge record was based on this evidence. |
| `RESOLVED_BY` | Assumption, Risk | GovernanceDecision, ExperimentResult, ObservationRecord | N:1 | The assumption was resolved or the risk was mitigated by this artifact. |
| `REOPENS` | Evidence entity, ObservationRecord | GovernanceDecision, Knowledge entity | N:N | New evidence triggers reconsideration of a prior decision or record. |
| `PROMOTES_TO` | Knowledge entity (lower gravity) | Knowledge entity (higher gravity) | N:1 | The source concept was promoted to a higher-authority knowledge type. Requires evidence. |
| `CONTRIBUTED_TO_GENOME` | Pattern, AntiPattern, ArchitecturalPrinciple, Risk | Engineering Genome (AC-0002 entity) | N:1 | This entity contributed to the Engineering Genome. |

**Integrity constraints:**
- `DERIVES_FROM` must terminate at a `FoundationalConcept` or the `Constitution`; orphaned
  derivation chains are a graph integrity violation.
- `TRACES_TO` must be completable: every significant implementation can, in principle, be
  traced to a constitutional basis. If the trace is broken, it is an open risk (see ONTO-0003).
- `LINKED_TO` is a last resort. If a more specific relationship exists, it must be used.
- `PROMOTES_TO` requires `evidence_refs` and must not skip hierarchy levels (e.g., a bare
  observation cannot be directly promoted to a `FoundationalConcept`).
- `REOPENS` creates a review trigger but does not itself revoke or supersede the prior decision.

---

### 3.5 Structural and Dependency Relationships

These relationships describe structural composition and technical dependencies.

| Relationship | Source | Target | Cardinality | Description |
|---|---|---|---|---|
| `DEPENDS_ON` | Entity | Entity | N:N | The source cannot function correctly without the target. |
| `PART_OF` | Entity | Entity | N:1 | The source is a component of the target. |
| `BELONGS_TO` | Entity | Organization, Project | N:1 | The entity is scoped to this organization or project. |
| `INSTANTIATES` | Entity | Pattern, ArchitecturalPrinciple | N:1 | The entity is a concrete instance or application of the target. |
| `HAS_VERSION` | versioned Entity | VersionHistory | 1:1 | The entity's version history. |
| `STORED_IN` | Artifact | ArtifactStore, Repository | N:1 | The artifact is persisted in this store or repository. |

**Integrity constraints:**
- `DEPENDS_ON` cycles are flagged and must be reviewed; they are not automatically forbidden
  (some mutual dependencies are valid) but must be explicitly acknowledged.
- `INSTANTIATES` requires that the source entity conforms to the pattern's invariants. A
  `ReviewRecord` should confirm this conformance for significant instantiations.
- `PART_OF` hierarchies must be acyclic.

---

## 4. Relationship Use Summary

| Category | Key relationships | Required evidence |
|---|---|---|
| Authority chain | `GOVERNS`, `DELEGATES_TO`, `AUTHORIZES` | Governance instrument reference |
| Execution | `EXECUTES_UNDER`, `PRODUCED`, `ASSIGNED_TO` | Task reference, delegation reference |
| Evaluation | `EVALUATES`, `VERIFIED_BY`, `EVIDENCES` | Evidence entity reference |
| Contradiction | `CONTRADICTS`, `REOPENS` | Evidence entity reference + `evidence_refs` |
| Knowledge traceability | `DERIVES_FROM`, `TRACES_TO`, `IMPLEMENTS` | Higher-layer concept reference |
| Evolution | `SUPERSEDES`, `PROMOTES_TO`, `AMENDS` | Evidence and prior-state reference |
| Structural | `DEPENDS_ON`, `PART_OF`, `INSTANTIATES` | Conformance or dependency justification |

---

## 5. Prohibited Patterns

The following relationship uses are explicitly prohibited:

1. **Implicit authority by proximity** — an entity is not authorized simply because it exists in
   the same directory or file as an authorized entity.
2. **Self-verification** — an Executor asserting `VERIFIED_BY` for its own Material Action
   without an independent Evaluator.
3. **Orphaned derivation** — an `ArchitecturalPrinciple` or `Pattern` without a `DERIVES_FROM`
   link to a `FoundationalConcept` or the `Constitution`.
4. **Silent supersession** — a `SUPERSEDES` relationship without `evidence_refs` showing why the
   change was made.
5. **Bare `LINKED_TO`** — using `LINKED_TO` when a more specific relationship type exists.
