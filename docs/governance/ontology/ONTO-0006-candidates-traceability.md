# ONTO-0006 — Architectural Candidates and Traceability

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Architecture Candidate Evaluations

Every candidate record has a stable `candidate_id`, canonical name, status, proposer and proposal
date, definition, problem, scope and non-goals, constitutional and Foundational Concept
alignment, supporting and contradicting evidence, independent and failed applications, reuse
events, Knowledge Gravity and Genome states, promotion target, reopening conditions, linked
issues/decisions/PRs/releases, and last/next review dates. Conversational support alone is never
promotion evidence.

Issue #16 requires **AC-0005 Explicit Relationships** and **AC-0006 Semantic Inheritance** to
receive an explicit `adopt / modify / reject` decision only after repeated evaluation. This
Ontology records their current evaluation and does not substitute initial design support for
cross-workstream evidence.

The canonical candidate lifecycle is:

```
PROPOSED → OBSERVED → VALIDATING → QUALIFIED → PROMOTION_REVIEW → ADOPTED
```

Alternative outcomes are `REJECTED`, `DEFERRED`, `NEEDS_EVIDENCE`, `WITHDRAWN`,
`SUPERSEDED`, and `RETIRED`. Neither candidate may be promoted in this document alone.
Promotion to `FoundationalConcept` requires a separate governance decision supported by repeated
evidence and every gate in ONTO-0004 §1.8.

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

**Candidate status after Ontology phase:** `VALIDATING`
**Current evaluation outcome:** `NEEDS_EVIDENCE` (canonical spelling per ONTO-0003 §8); adopt/modify/reject is deferred until
the repeated-evaluation gate is met.

**Promotion criteria:** Demonstrate that explicit relationships reduce implementation ambiguity,
improve query determinism, and support evidence-backed impact analysis across at least three
independent architectural workstreams, while satisfying every gate in ONTO-0004 §1.8.
*Independence is defined (DR-0004 P-7): a workstream is independent of another when it has a
different initiating issue, a different primary Executor session, and no shared draft lineage.
This definition applies to every promotion gate in this family that requires independence.*

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
| Complexity risk | Deep inheritance hierarchies may cause unclear rule applicability. The entity families are currently shallow (one root + eight families + leaf types). If this depth increases, semantic inheritance may create more confusion than it resolves. |
| Counter-evidence | The current document-based representation (Markdown files) does not enforce inheritance programmatically. Semantic inheritance is a logical model, not yet an enforced implementation constraint. This is a weakness in its current evidence base. |

**Candidate status after Ontology phase:** `VALIDATING`
**Current evaluation outcome:** `NEEDS_EVIDENCE` (canonical spelling per ONTO-0003 §8); adopt/modify/reject is deferred until
the repeated-evaluation gate is met.

**Promotion criteria:** Demonstrate that inheritance-based field sharing reduces specification
duplication and constraint ambiguity in at least three independent architectural workstreams. The
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

Per TARP-0001 — actual title "**Traceability and Review Protocol**"
([`docs/agentic3/TARP-0001-traceability-protocol.md`](../../agentic3/TARP-0001-traceability-protocol.md),
status **Proposed**), whose review discipline is implemented by the Active
standard [`STD-0002`](../playbook/STD-0002-traceable-architecture-reviews.md);
the naming/status resolution is decision **P-4** — every significant
architectural proposal requires a traceable chain from implementation to
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
- [ ] run any canonical query against a populated graph;
- [ ] trace any implementation to its constitutional basis;
- [ ] identify the status (`VALIDATING`, evidence required) of AC-0005 and AC-0006.

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

## 3. Architecture Candidate Register (pointer)

**The single candidate register is
[`ACR-0001`](../knowledge/ACR-0001-architectural-candidate-register.md).**
This document no longer maintains its own status table: a second register in
a Draft document was itself the "silent status assignment" this document's
mechanics forbid (recorded and resolved in
[`PHASE0-RECONCILIATION.md`](../../agentic3/PHASE0-RECONCILIATION.md) §2).
Candidates this document introduced (AC-0005 Explicit Relationships,
AC-0006 Semantic Inheritance) are recorded there, alongside AC-0003, with
their statuses. The recorded adoption status of AC-0001/AC-0002 is disputed
by those documents' own headers; resolution is reserved to the Principal
(decisions P-1/P-2). This section's former table is preserved in git
history.

---

## 4. Open Risks

| ID | Risk | Probability | Impact | Mitigation | Review trigger |
|---|---|---|---|---|---|
| RSK-ONT-001 | Ontology entity coverage is incomplete — later engines introduce types that cannot be mapped to existing families | Medium | High — forces retroactive model revision that may break existing relationships | Defined Type Completeness Requirement (ONTO-0001 §4); new types are added via authorized Ontology revision | First instance of a force-fit classification in any subsequent engine design |
| RSK-ONT-002 | Knowledge Gravity scoring becomes arbitrary — evidence events without inspectable external references inflate gravity scores | Low | High — undermines AC-0001 and the entire knowledge promotion system | Anti-gaming safeguards in ONTO-0004 §1.7; `foundational` level requires governance decision, not evidence count alone | First gravity review that fails to produce inspectable evidence references |
| RSK-ONT-003 | AC-0005 and AC-0006 accumulate insufficient evidence — both remain `VALIDATING` indefinitely, leaving a gap in the governing hierarchy between Ontology and Patterns | Medium | Medium — the gap is acknowledged but creates uncertainty for engine designers | Review deadline tied to the third engine design phase; at that point an explicit adopt/modify/reject decision is required regardless of evidence | Completion of the third independent engine design phase |
| RSK-ONT-004 | Inheritance hierarchies (AC-0006) become a source of classification disputes — entity types are forced into families that don't cleanly fit | Medium | Medium — causes ambiguity in lifecycle and query behavior | Modify conditions for AC-0006 include interface-based contracts as an alternative; shallow hierarchy (≤3 levels) enforced | First classification dispute during an engine design |
| RSK-ONT-005 | Open PRs (#11, #13, #14, #15) contain overlapping content — merging them after this PR may require reconciliation | High — all 4 PRs exist now | Low to Medium — conflicts are documentation-level, not logic-level | This PR is isolated to `docs/governance/ontology/`; no files modified in `docs/governance/knowledge/` or existing playbook docs | Review of each PR's changed files before merge |
| RSK-ONT-006 | Traceability chains are broken in early implementations — no mechanism enforces TARP compliance before merge | Medium | Medium — gaps accumulate until an audit discovers them | Q-009 TARP traceability query defined; GI-011 registers broken traceability as a Risk entity | First PR that includes a `TRACES_TO` chain audit in its review packet |

---

## 5. Engine Crosswalk

The shared ontology does not transfer authority between engines. Engine ownership means primary
responsibility for authoring records; all durable records remain subject to typed relationships,
provenance, governance, and historical continuity.

| Engine / domain | Primary records authored | Primary relationships | Forbidden authority |
|---|---|---|---|
| Memory | entity versions, provenance, FR, RM, IER, RL, TET, checkpoints | `RECORDS`, `DERIVES_FROM`, `LEARNED_FROM` | May not promote knowledge, determine truth, or confer authority. |
| Knowledge | claims, lessons, patterns, candidates, gravity events, genome revisions | `EXTRACTS`, `STRENGTHENS`, `WEAKENS`, `CONTRADICTS`, `CONTRIBUTED_TO_GENOME` | May not ratify, authorize, or silently promote. |
| Governance | policy, permission, gate, approval, delegation, governance decisions | `GOVERNS`, `AUTHORIZES`, `PROHIBITS`, `DELEGATES_TO`, `REVOKES`, `SUPERSEDES` | May not fabricate evidence or execute governed work. |
| Verification | test, CI, review, and verification results | `EVALUATES`, `EVIDENCES`, `SUPPORTS`, `CONTRADICTS`, `SATISFIES`, `FAILS` | May not authorize action or redefine criteria after results are known. |
| Assurance | assurance results and readiness findings | `ASSURES`, `REOPENS`, `REQUIRES_GATE` | May not execute work, mutate evidence, or replace Principal authority. |
| Evolution | change proposals, experiments, reopening proposals | `REOPENS`, `DERIVES_FROM`, `APPLIED_IN` | May propose but not amend, ratify, deploy, or promote its own proposal. |
| Runtime | runtime events, executions, dispatch and telemetry records | `OBSERVES`, `ASSIGNED_TO`, `EXECUTES`, `PRODUCED`, `CONSUMES`, `BLOCKS` | May enforce recorded authority but may not create or resolve it. |

### 5.1 Mutation boundaries

| Entity family | Memory | Knowledge | Governance | Verification | Assurance | Evolution | Runtime |
|---|---:|---:|---:|---:|---:|---:|---:|
| Entity versions / provenance | C/U | R | R | R | R | propose | R |
| Knowledge / gravity / genome | R | C/U | authorize/promote | R | R | propose | R |
| Governance / authority / gates | R | R | C/U/authorize | R | R | propose | enforce |
| Evidence / verification | preserve | R | R | C/verify | R | R | C/read |
| Assurance results | R | R | R | R | C/U | R | enforce |
| Work / execution / artifacts | preserve | R | authorize | verify | assess | propose | C/U |

`C/U` means create or update lifecycle metadata by adding a new version or event, never rewriting
append-only history. `authorize`, `verify`, and `promote` are intentionally separate capabilities.

### 5.2 Required handoffs

1. Governance gives Runtime a bounded authorization, gates, expiry, and stop conditions.
2. Runtime gives Verification artifacts, execution evidence, criteria, and provenance.
3. Verification gives Assurance results, unknowns, contradictions, scope, and confidence limits.
4. Assurance gives Governance a ready, not-ready, or more-evidence-required result with rationale.
5. Every engine gives Memory context-complete event and decision records.
6. Memory gives Knowledge validated records with provenance and lifecycle status.
7. Knowledge gives Evolution patterns, contradictions, gravity changes, and genome gaps.
8. Evolution gives Governance proposals only; it never mutates a higher layer directly.
