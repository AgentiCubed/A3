# ONTO-0006 — Architectural Candidates and Traceability

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Architecture Candidate Evaluations

Issue #16 requires explicit `adopt / modify / reject` candidate decisions for two new
architectural candidates — **AC-0005 Explicit Relationships** and **AC-0006 Semantic
Inheritance** — as part of the Ontology design phase.

Per the Architectural Candidate lifecycle (Issue #12), candidates are:

```
Proposed → Under Review → Adopted → Superseded → Retired
```

Neither may be promoted to `Adopted` in this document alone. Promotion to `FoundationalConcept`
requires a separate governance decision by the Principal, supported by evidence from multiple
architecture phases.

---

### AC-0005 — Explicit Relationships

**Candidate thesis:** All semantic connections between Agentic³ entities should be expressed
as named, typed, and machine-traversable relationships rather than inferred from document
proximity, file structure, or prose description.

**First introduced:** Issue #16 Ontology design phase, 2026-07-16.

**Evidence gathered during Ontology design:**

| Evidence type | What was observed |
|---|---|
| Design necessity | Every canonical query in ONTO-0005 requires named relationship traversal to produce auditable results. Implicit proximity would make Q-002 (impact), Q-003 (contradiction), Q-008 (upward compatibility), and Q-009 (TARP traceability) non-deterministic. |
| Constitution grounding | Constitution Art. IV §2 requires preserving Evidence to identify each Material Action, its originating Delegation, and the Principal from whom authority derived. This is impossible without explicit relationships. |
| Existing practice | The institutional memory system already uses explicit record linkage (linked FR/RM pairs, IER stage sequences). The Ontology formalizes what was already an emerging pattern. |
| Negative evidence | No existing design in the repository relies on implicit entity proximity as the primary mechanism for resolving relationships. |

**Candidate status after Ontology phase:** `Under Review`

**Promotion criteria:** Demonstrate that explicit relationships reduce implementation ambiguity,
improve query determinism, and support evidence-backed impact analysis across at least two
independent engine design phases (e.g., Memory Engine and Governance Engine).

**Modify conditions:** If explicit relationship modeling is found to impose
disproportionate overhead for well-understood local relationships (e.g., a failure record
linking to its own sub-fields), the candidate may be modified to define a scope threshold
distinguishing local vs. cross-entity relationships.

**Rejection conditions:** If a later engine design demonstrates that implicit relationships
produce equivalent or better determinism without sacrificing Constitutional compliance, this
candidate may be rejected. Evidence must be provided.

**Reopening conditions:** Any evidence that implicit relationships caused an audit failure,
a missing traceability chain, or an impact analysis error is a reopening trigger.

---

### AC-0006 — Semantic Inheritance

**Candidate thesis:** Agentic³ entity types should form explicit inheritance hierarchies rather
than flat ad-hoc categorizations, sharing lifecycle behavior, query semantics, and field
requirements via their parent type.

**First introduced:** Issue #16 Ontology design phase, 2026-07-16.

**Evidence gathered during Ontology design:**

| Evidence type | What was observed |
|---|---|
| Natural hierarchy observation | The entity model in ONTO-0001 naturally groups into families: all Knowledge entities share `knowledge_gravity` eligibility; all Actor entities share authority-constraint rules; all Evidence entities share append-only and self-attestation rules. These behaviors would be repeated for each type if inheritance were not used. |
| DRY argument | Without inheritance, the `VerificationRecord` constraint (requiring an Evidence reference) would need to be stated redundantly for every entity type that might claim verification. |
| Complexity risk | Deep inheritance hierarchies may cause unclear rule applicability. The entity families are currently shallow (one root + seven families + leaf types). If this depth increases, semantic inheritance may create more confusion than it resolves. |
| Counter-evidence | The current document-based representation (Markdown files) does not enforce inheritance programmatically. Semantic inheritance is a logical model, not yet an enforced implementation constraint. This is a weakness in its current evidence base. |

**Candidate status after Ontology phase:** `Under Review`

**Promotion criteria:** Demonstrate that inheritance-based field sharing reduces specification
duplication and constraint ambiguity in at least two independent engine specifications. The
inheritance depth must remain manageable (no more than three levels: root → family → leaf type)
without requiring exceptions.

**Modify conditions:** If a strict inheritance hierarchy proves too rigid for certain entity
families, the candidate may be modified to support interface-based rather than class-based
inheritance (entities conforming to named behavior contracts without requiring a single
ancestry chain).

**Rejection conditions:** If inheritance hierarchies are found to require frequent exceptions
that undermine their simplifying purpose, or if an engine design requires entity types that
fit no existing family without forced classification, this candidate should be rejected in
favor of a flat namespace with explicit behavior contracts.

**Reopening conditions:** Any engine design that introduces entity types requiring multi-family
inheritance is a reopening trigger for reviewing whether the current inheritance model is
sufficient.

---

## 2. TARP-0001 Traceability for the Ontology

Per TARP-0001 (Traceable Architecture Review Process, formalized in Issue #12), every
significant architectural proposal requires a traceable chain from implementation to
constitutional basis.

The Ontology itself is a significant architectural specification. The traceability chain is:

### 2.1 Constitutional Alignment

| Constitutional basis | How the Ontology honors it |
|---|---|
| Art. IV §2 — Evidence must be preserved to identify Material Actions, originating Delegation, and authority chain | `ONTO-0002`: `EVIDENCES`, `VERIFIED_BY`, `DELEGATES_TO`, and `AUTHORIZES` relationships; `ONTO-0003` GI-008 requiring evidence for every VerificationRecord |
| Art. V §3 — Executor shall not be sole Evaluator | `ONTO-0003` GI-005: executor/evaluator distinction enforced as graph integrity rule |
| Art. VI §1, §3, §5 — Evidence requirements for Material Actions | `ONTO-0001` Evidence entity family; `ONTO-0003` GI-008, GI-009 |
| Art. VII §2 — No self-expansion of authority | `ONTO-0001` Actor constraints; `ONTO-0002` `DELEGATES_TO` integrity rule |
| Art. XII §4 — Historical continuity; supersession preserves prior text | `ONTO-0003` GI-007, lifecycle supersession rules, versioning semantics |

No constitutional article is contradicted by the Ontology. The Ontology is a subordinate
specification instrument, not a constitutional revision.

### 2.2 Foundational Concept Alignment

| Foundational Concept | How the Ontology serves it |
|---|---|
| AC-0001 — Knowledge Gravity | `ONTO-0004` §1: full KnowledgeGravityMetadata model; gravity levels with evidence thresholds; anti-gaming safeguards; promotion and demotion rules all implemented in the Ontology |
| AC-0002 — Engineering Genome | `ONTO-0004` §2: GenomeMembershipRecord; genome element types; membership lifecycle; revision history; interaction with Knowledge Gravity |
| AC-0004 — Separation of Decision and Execution (Candidate) | `ONTO-0001` §2.1 Actor Entities; `ONTO-0003` GI-005 (executor ≠ evaluator); `ONTO-0002` `EVALUATES` integrity constraint |

No Foundational Concept is contradicted. AC-0005 and AC-0006 are introduced for evaluation,
not adopted, consistent with the candidate lifecycle.

### 2.3 Architectural Principle Alignment

No Architectural Principles are adopted yet (that layer sits below the Ontology in the
hierarchy). The Ontology is the pre-principle layer. Principles will be derived from the
Ontology in subsequent design phases.

### 2.4 Pattern Alignment

The following patterns are instantiated by the Ontology:

| Existing pattern or practice | Instantiated where |
|---|---|
| Failure-first institutional memory | `ONTO-0001` Evidence entity family; `ONTO-0004` gravity demotion on failure |
| Gate workflow (diagnose/edit/verify) | `ONTO-0001` `TaskPacket` and `ReviewPacket` governance entities; `ONTO-0003` verification lifecycle |
| Append-only audit records | `ONTO-0003` GI-012; Evidence entity constraints; temporal entity constraints |
| Explicit authority chains | `ONTO-0002` §3.1 Authority relationships; `ONTO-0003` GI-002 |
| Provider-neutral adapters | `ONTO-0001` `ProviderAdapter` system entity |

### 2.5 Verification Plan

The Ontology specification is complete when a future contributor can, without conversational
memory:

- [ ] identify every entity type and its parent family;
- [ ] identify every relationship type, its source and target constraints, and its integrity rules;
- [ ] determine the lifecycle state and valid transitions for any entity;
- [ ] determine the Knowledge Gravity level and promotion/demotion rules for any knowledge entity;
- [ ] determine whether an entity is in the Engineering Genome;
- [ ] run any of the eleven canonical queries against a populated graph;
- [ ] trace any implementation to its constitutional basis;
- [ ] identify the status (Under Review, evidence required) of AC-0005 and AC-0006.

### 2.6 Reopening Conditions

The Ontology must be reopened under any of the following conditions:

1. A new engine design (Memory, Verification, Assurance, Evolution) introduces entity types
   that do not fit existing families without forced classification.
2. AC-0005 or AC-0006 accumulate sufficient evidence for promotion or are clearly rejected
   based on cross-phase evidence.
3. A constitutional amendment changes the Evidence or Verification requirements in a way that
   conflicts with this Ontology's evidence models.
4. A new Foundational Concept is adopted whose requirements are not served by the current
   entity model or relationship vocabulary.
5. The Knowledge Gravity model is found to enable scoring theater despite the anti-gaming
   safeguards; a redesign of gravity metadata is required.

---

## 3. Architecture Candidate Register Update

The following candidates are now in the register as a result of the Ontology design phase.
This table supplements the Architectural Candidate Register (ACR-0001) that will be formally
maintained once the PR establishing it is merged.

| ID | Title | Status | Introduced in | Promotion criteria summary |
|---|---|---|---|---|
| AC-0001 | Knowledge Gravity | Adopted (Foundational Concept) | Issue #12 | Already adopted by Principal; see ACR-0001 in PR#14. |
| AC-0002 | Engineering Genome | Adopted (Foundational Concept) | Issue #12 | Already adopted by Principal; see ACR-0001 in PR#14. |
| AC-0003 | Architectural Contracts | Proposed (Candidate) | Issue #12 | Formalized as entity type `ArchitecturalContract` (CON-NNNN) in ONTO-0001; promotion criteria: demonstrate value in binding subsystem invariants across two engine designs. |
| AC-0004 | Separation of Decision and Execution | Proposed (Foundational Candidate) | Issue #12 | Supported by GI-005 and the Actor entity constraints in ONTO-0001; promotion requires evidence across multiple design phases. |
| AC-0005 | Explicit Relationships | Under Review | Issue #16 (this document) | Promote after evidence from two independent engine design phases. |
| AC-0006 | Semantic Inheritance | Under Review | Issue #16 (this document) | Promote after evidence from two independent engine design phases; modify conditions defined above. |

---

## 4. Open Risks

| ID | Risk | Probability | Impact | Mitigation | Review trigger |
|---|---|---|---|---|---|
| RSK-ONT-001 | Ontology entity coverage is incomplete — later engines introduce types that cannot be mapped to existing families | Medium | High — forces retroactive model revision that may break existing relationships | Defined Type Completeness Requirement (ONTO-0001 §4); new types are added via authorized Ontology revision | First instance of a force-fit classification in any subsequent engine design |
| RSK-ONT-002 | Knowledge Gravity scoring becomes arbitrary — evidence events without inspectable external references inflate gravity scores | Low | High — undermines AC-0001 and the entire knowledge promotion system | Anti-gaming safeguards in ONTO-0004 §1.7; `foundational` level requires governance decision, not evidence count alone | First gravity review that fails to produce inspectable evidence references |
| RSK-ONT-003 | AC-0005 and AC-0006 accumulate insufficient evidence — both remain `Under Review` indefinitely, leaving a gap in the governing hierarchy between Ontology and Patterns | Medium | Medium — the gap is acknowledged but creates uncertainty for engine designers | Review deadline tied to the third engine design phase; at that point an explicit adopt/modify/reject decision is required regardless of evidence | Completion of the third independent engine design phase |
| RSK-ONT-004 | Inheritance hierarchies (AC-0006) become a source of classification disputes — entity types are forced into families that don't cleanly fit | Medium | Medium — causes ambiguity in lifecycle and query behavior | Modify conditions for AC-0006 include interface-based contracts as an alternative; shallow hierarchy (≤3 levels) enforced | First classification dispute during an engine design |
| RSK-ONT-005 | Open PRs (#11, #13, #14, #15) contain overlapping content — merging them after this PR may require reconciliation | High — all 4 PRs exist now | Low to Medium — conflicts are documentation-level, not logic-level | This PR is isolated to `docs/governance/ontology/`; no files modified in `docs/governance/knowledge/` or existing playbook docs | Review of each PR's changed files before merge |
| RSK-ONT-006 | Traceability chains are broken in early implementations — no mechanism enforces TARP compliance before merge | Medium | Medium — gaps accumulate until an audit discovers them | Q-009 TARP traceability query defined; GI-011 registers broken traceability as a Risk entity | First PR that includes a `TRACES_TO` chain audit in its review packet |
