# ONTO-0003 — Integrity and Lifecycle

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Graph Integrity Rules

These rules govern the entire Agentic³ entity graph. A graph that violates any of these rules
is in an invalid state that must be corrected before work proceeds.

### GI-001 — Stable Identifier Required Before Reference

An entity must have a stable identifier before any other entity may reference it. An entity
referenced by identifier alone (without a resolvable record) is an integrity violation.

### GI-002 — Authority Must Trace to a Principal

Every entity's `authority_refs` must trace, through a chain of governance relationships, to a
`Principal`. A chain that terminates at a `PlaybookDocument` or `ArchitectureDecisionRecord`
without a further link to a ratifying Principal is incomplete.

Authority chains are verified by traversing `AUTHORIZES`, `RATIFIED_BY`, and `DELEGATES_TO`
relationships to their origin.

### GI-003 — No Cycles in Supersession or Derivation

`SUPERSEDES` and `DERIVES_FROM` graphs must be acyclic. A cycle (e.g., A supersedes B and B
supersedes A) indicates a logic error that must be corrected.

`PART_OF` hierarchies must also be acyclic.

Exception: mutual `DEPENDS_ON` relationships are not automatically forbidden but must be
explicitly acknowledged (see ONTO-0002 §3.5).

### GI-004 — Evidence Must Precede or Be Contemporaneous With the Claim

An evidence entity used to support a verification or knowledge claim must have a `created_at`
timestamp at or before the claim's `asserted_at` timestamp. Future-dated evidence is not valid
evidence for a past claim.

### GI-005 — Executor and Evaluator Must Differ

For any Material Action, the entity asserting `EVALUATES` must differ from the entity asserting
`EXECUTES_UNDER` on the same action. This rule is unconditional (Constitution Art. V §3).

If a boundary requires the same entity to both execute and evaluate, the work must be escalated
to the responsible Principal before proceeding.

### GI-006 — Delegation Chain Must Terminate at a Principal

A `Delegation` that traces only to another `Delegation` without eventually reaching a
`Principal` is invalid. Delegation chains are not permitted to be circular.

### GI-007 — Supersession Preserves Prior Content

A `SUPERSEDES` relationship must not erase the prior entity. Both entities must remain
navigable. The superseded entity's `lifecycle_state` is updated to `superseded`; its content
is not modified.

### GI-008 — Verification Requires Evidence

A `VerificationRecord` must reference at least one `Evidence` entity via an `EVIDENCES`
relationship. A `VerificationRecord` with no evidence references is not a valid verification.

### GI-009 — Epistemic States Must Remain Distinct

In any knowledge entity, the fields carrying facts, interpretations, hypotheses, evidence,
confidence, and authority decisions must be distinct. A single prose block that conflates these
states is a model violation that must be corrected before the record is used as evidence.

### GI-010 — Pattern Requires Multiple Application Events

A `Pattern` entity must reference at least two independent application events via its
`application_evidence` field. A single successful application produces an `Assumption` or
`Risk`, not a `Pattern`.

### GI-011 — Broken Traceability Is a Registered Risk

If a `TRACES_TO` path cannot be completed (e.g., an implementation cannot be traced to a
`FoundationalConcept` or constitutional article), this gap must be registered as a `Risk`
entity. It may not be silently ignored.

### GI-012 — Append-Only Entities Shall Not Be Modified

Entities designated append-only in ONTO-0001 — `AuditEvent`, `Evidence` families, governance
entity bodies, temporal entities — must not be modified after creation. Corrections are added
as new linked entities with `SUPERSEDES` relationships.

### GI-013 — Durable Architectural Artifacts Must Not Be Orphaned

Every durable architectural artifact must have at least one incoming or outgoing semantic
relationship beyond storage metadata. An orphan is registered as informational debt and may not
be treated as authoritative.

---

## 2. Lifecycle States

All entities use one of the following lifecycle states unless a specific entity type defines a
narrower operational status (which supplements, not replaces, this vocabulary).

| State | Meaning |
|---|---|
| `draft` | Written but not yet ready for use; may be incomplete or awaiting review. |
| `active` | Current, usable record; may still be accumulating supporting evidence. |
| `validated` | Evidence or repeated reuse has raised confidence to a level warranting broader use. |
| `superseded` | Replaced by a newer entity that preserves the prior state and records the reason. |
| `retired` | Intentionally kept for historical continuity but no longer expected to guide work. |

The canonical lifecycle is:

```
draft → active → validated → superseded | retired
```

Additional transitions:

```
draft → retired        (abandoned before activation)
active → superseded    (replaced before full validation)
active → retired       (explicitly decommissioned)
validated → superseded (replaced despite validation)
validated → retired    (decommissioned from active use)
```

### Lifecycle state constraints

- A transition to `superseded` must be accompanied by a `SUPERSEDES` relationship from the
  new entity to this one, and `evidence_refs` explaining the reason.
- A transition to `retired` must be recorded as a `LifecycleTransition` entity with a
  `triggered_by` reference (decision, evidence, or governance record).
- `draft` entities may not be used as authoritative references. They may be referenced as
  in-progress work but must not be cited as settled authority.
- `superseded` entities remain readable and referable; their content is not hidden. They carry
  a `superseded_by` reference to the new entity.
- `retired` entities remain permanently readable for historical continuity but are explicitly
  excluded from normal query result sets (see ONTO-0005).

---

## 3. Lifecycle Transition Constraints by Entity Family

| Family | May be superseded | May be retired | Transition triggers |
|---|---|---|---|
| Actor | Yes (role ends; new delegation starts) | Yes | Delegation expiry, revocation, role change |
| System | Yes (component replaced) | Yes | Architecture decision, migration |
| Knowledge | Yes — new entity preserves prior | Yes — historical continuity kept | Evidence change, governance decision, error correction |
| Artifact (content-addressed) | No — immutable once hashed | N/A | N/A |
| Artifact (non-content-addressed) | Yes | Yes | New version produced |
| Evidence | No — append-only | No | N/A |
| Governance | Yes — amendment or supersession | Yes | Amendment process (Constitution), new decision |
| Temporal | No — immutable record of what happened | No | N/A |

---

## 4. Identity Semantics

### 4.1 Stable Identifier Namespaces

| Prefix | Entity family | Notes |
|---|---|---|
| `AC-NNNN` | FoundationalConcept, ArchitecturalCandidate | Architectural Candidate register |
| `ADR-NNNN` | ArchitectureDecisionRecord | Architecture decisions |
| `DR-NNNN` | GovernanceDecision | Governance-namespace decisions |
| `FR-NNNN` | FailureRecord | |
| `RM-NNNN` | Rumination | |
| `IER-NNNN` | IdeaEvolutionRecord | |
| `RL-NNNN` | ReasoningLedger | |
| `TET-NNNN` | TETCapsule | |
| `PAT-NNNN` | Pattern | |
| `AP-NNNN` | AntiPattern | |
| `RSK-NNNN` | Risk | |
| `ASM-NNNN` | Assumption | |
| `EXP-NNNN` | Experiment | |
| `USR-NNNN` | UnexpectedSuccessRecord | |
| `ARC-NNNN` | ArchitecturalPrinciple | |
| `CON-NNNN` | ArchitecturalContract | |
| `A-NNNN` | ConstitutionalAmendment | |
| `POL-NNNN` | Policy document | |
| `PROC-NNNN` | Procedure document | |
| `STD-NNNN` | Standard document | |
| `TPL-NNNN` | Template document | |
| `ONTO-NNNN` | Ontology document | |

Identifiers within a namespace are assigned sequentially and are never reused. A `NNNN` slot
that is retired or superseded keeps its number; the next assignment receives the next available
number.

### 4.2 Identifier Stability Rule

Once an entity has been referenced by another entity, its identifier must not change. If a
canonical name changes, the identifier remains stable; the new name is recorded in
`canonical_name` and the change is added to `version_history`.

### 4.3 Identity vs. Version

Entity identity persists across revisions. Each revision has a distinct `version_id`, while all
versions retain the same stable `entity_id`. `current_version_id` identifies the current revision,
and `version_history` preserves prior revisions as append-only records.

A new entity with a new `entity_id` is created only when the successor is conceptually distinct,
rather than a revision of the same entity. In that case the new entity `SUPERSEDES` the prior
entity, and both identifiers remain stable and referable.

---

## 5. Versioning Semantics

### 5.1 Version Identity Fields

For versioned entity types:

| Field | Description |
|---|---|
| `version_id` | Stable identifier unique to this revision. |
| `version.number` | Semantic version (`major.minor.patch`) or sequence number. |
| `version.status` | `draft`, `active`, `validated`, `superseded`, `retired`. |
| `version.effective_date` | Date this version became authoritative. |
| `version.parent_version_ids` | One or more parent versions from which this revision derives. |
| `version.authored_by` | Actor responsible for the revision. |
| `version.review_authority` | Governance reference authorizing review or adoption. |
| `version.change_summary` | Summary and change classification for the revision. |
| `version.evidence_refs` | Evidence supporting the revision. |
| `version.superseded_by` | Reference to the version that superseded this one. |
| `version.compatibility_status` | Compatibility with the Constitution and Foundational Concepts. |
| `version.reopening_conditions` | Conditions that require the revision to be reconsidered. |

### 5.2 Version Numbering Rules

- Governance documents (Constitution, amendments, decisions, playbook) use sequential version
  numbers (`v1.0`, `v1.1`, `v2.0`).
- Knowledge records use their sequence identifier (`FR-0001`, `FR-0002`); versions of the same
  record use revision notation (`FR-0001 rev 2`).
- Software artifact versions follow semantic versioning.

### 5.3 Change Classes

Every version records the highest applicable change class:

| Class | Meaning |
|---|---|
| `editorial` | Wording or formatting with no semantic change. |
| `clarifying` | Resolves ambiguity without changing authority or intended behavior. |
| `behavioral` | Changes expected system behavior. |
| `architectural` | Changes boundaries, contracts, entities, or relationships. |
| `governance` | Changes authority, obligations, gates, or permission semantics. |
| `constitutional` | Changes constitutional authority through the amendment process. |

An entity may not self-declare a lower class when evidence shows a higher-impact change.

### 5.4 Breaking Version Changes

A breaking change to a governance document or standard — one that changes acceptance
conditions, authority delegation, or constitutional standing — requires a new entity with a
new identifier (not a revision of the prior entity). The prior entity is superseded and
preserved.

Non-breaking clarifications and corrections create a new immutable version of the same entity.
The correction is annotated and the prior version remains unchanged.

---

## 6. Provenance Semantics

Provenance records the origin of an entity, not just its author.

| Field | Description |
|---|---|
| `provenance.created_by` | The actor who created the entity. |
| `provenance.authority_basis` | The governance relationship (delegation, decision, ratification) that authorized creation. |
| `provenance.source_artifacts` | If derived from other entities, the source references. |
| `provenance.context` | The issue, PR, CI run, or session that produced this entity. |
| `provenance.created_at` | Immutable creation timestamp. |

**Provenance constraints:**
- Provenance is set at creation and is immutable.
- If provenance was recorded incorrectly, an annotation is added to the entity's
  `version_history`; the original `provenance` field is not overwritten.
- An entity without a valid `authority_basis` in its provenance has unknown authority status
  and must be flagged for review before use.

---

## 7. Authority and Temporal Resolution

Authority is never inferred from document type, path, age, popularity, or confidence. Resolution
follows active constitutional authority, ratified amendments, authorized governance decisions,
active policies or standards, accepted architecture decisions, approved patterns or procedures,
then implementation evidence. Every step still requires an explicit relationship.

When active authority paths conflict, the result is `CONFLICT` until Governance records an
authorized interpretation or supersession. Runtime components may report but may not resolve the
conflict.

Every query whose answer may change over time accepts an `as_of` boundary and resolves entities,
relationship versions, authority, and validity intervals effective at that instant. Current state
never overwrites historical state.
