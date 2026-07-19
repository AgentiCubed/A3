# ONTO-0005 — Query Semantics

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Purpose

This document defines the canonical query semantics for the Agentic³ entity graph. The queries
here are defined in terms of entity types, relationship traversals, and filter conditions. They
do not specify a database, query language, or API. Implementations translate these semantics
into whatever storage and retrieval mechanism is appropriate.

---

## 2. Query Model

### 2.1 Query Structure

Every canonical query has:

| Field | Description |
|---|---|
| `query_name` | Stable identifier for the query pattern. |
| `question` | The natural-language question the query answers. |
| `starting_entity` | The entity type or identifier from which traversal begins. |
| `traversal` | The relationship types and directions to follow. |
| `filter` | Constraints on which entities to include (lifecycle state, entity type, date range, etc.). |
| `as_of` | Temporal boundary used to select then-effective entity and relationship versions. |
| `projection` | Which fields to include in the result. |
| `result_shape` | Whether the result is a list, tree, chain, or graph. |
| `excludes` | Entity types or lifecycle states to exclude from results by default. |

### 2.2 Default Exclusions

Unless explicitly overridden, all queries exclude:
- entities with `lifecycle_state = retired`;
- entities with `lifecycle_state = draft` from authority-chain results (drafts may appear in
  exploratory queries but are flagged);
- superseded entities (they appear only in historical and supersession queries where their
  inclusion is explicit).

---

## 3. Canonical Query Patterns

### Q-001 — Authority Chain Query

**Question:** What authorized this entity?

**Starting entity:** Any entity  
**Traversal:** Follow `authority → RATIFIED_BY → Principal` and `authority → AUTHORIZES ← Delegation → DELEGATES_TO ← Principal` backward to the originating Principal  
**Filter:** Active governance entities only  
**Result shape:** Chain from entity → governance instrument(s) → Principal  
**Use cases:** Audit trail; verifying that work was authorized; constitutional compliance review

**Required output fields:**
- entity identifier and type
- each governance instrument in the chain (GovernanceDecision, Delegation, TaskPacket)
- terminal Principal identifier
- whether the chain terminates cleanly at a Principal or is broken (broken = open risk per GI-002)

---

### Q-002 — Impact Query

**Question:** What depends on this entity, directly or transitively?

**Starting entity:** Any entity (typically a Knowledge entity, ArchitecturalPrinciple, or ServiceComponent)  
**Traversal:** Follow `DEPENDS_ON`, `DERIVES_FROM`, `IMPLEMENTS`, `INSTANTIATES`, `PART_OF` (reversed) outward from the entity  
**Filter:** Active entities; optionally filtered by entity family  
**Result shape:** Dependency tree or graph  
**Use cases:** Change impact assessment; risk analysis; understanding blast radius of a proposed change

**Required output fields:**
- each dependent entity's identifier, type, and lifecycle state
- the relationship type connecting each dependent to the source
- depth from source (direct vs. transitive)
- whether any dependent is a `FoundationalConcept`, `Constitution`, or `GovernanceDecision`
  (constitutional impact flag)

---

### Q-003 — Contradiction Query

**Question:** What contradicts this entity's claims, and how strong is the contradiction?

**Starting entity:** A Knowledge entity, GovernanceDecision, or ArchitectureDecisionRecord  
**Traversal:** Follow `CONTRADICTS` relationships targeting the entity; follow `REOPENS` relationships targeting the entity  
**Filter:** Active evidence entities; active and superseded knowledge entities (superseded contradictions matter for history)  
**Result shape:** List sorted by `evidence_refs` count (descending)  
**Use cases:** Reviewing whether a principle or decision is still valid; identifying when a reopening condition has been met

**Required output fields:**
- each contradicting entity's identifier, type, and lifecycle state
- the evidence references supporting each contradiction
- whether any contradiction has triggered a review

---

### Q-004 — Authority Query

**Question:** Who has authority over this entity or action, and at what scope?

**Starting entity:** Any entity  
**Traversal:** Follow `GOVERNS`, `AUTHORIZES`, `DELEGATES_TO` to find the Principals and governance instruments with authority over the entity  
**Filter:** Active governance entities; non-expired Delegations  
**Result shape:** Set of (Principal, scope, authority_instrument) tuples  
**Use cases:** Determining who must approve a change; identifying authority gaps; escalation routing

**Required output fields:**
- each authority holder (Principal, Evaluator) and their scope
- the governance instrument granting that authority
- whether the authority is direct (Principal) or delegated (Executor with Delegation)
- expiry date of any Delegation

---

### Q-005 — Provenance Query

**Question:** Where did this entity come from, and what authorized its creation?

**Starting entity:** Any entity  
**Traversal:** Follow `provenance.authority_basis` to the governance instrument; follow `provenance.source_artifacts` to source entities; follow `provenance.created_by` to the creating actor  
**Filter:** All lifecycle states (provenance is historical and includes superseded entities)  
**Result shape:** Provenance chain  
**Use cases:** Audit; accountability; understanding how a knowledge claim was formed; tracing an artifact to its execution

**Required output fields:**
- `provenance.created_by` (actor)
- `provenance.authority_basis` (governance instrument)
- `provenance.source_artifacts` (source entities, if any)
- `provenance.context` (issue, PR, CI run)
- `provenance.created_at` (timestamp)

---

### Q-006 — Reuse Query

**Question:** How many times and in what contexts has this pattern or principle been applied?

**Starting entity:** Pattern, AntiPattern, ArchitecturalPrinciple, FoundationalConcept  
**Traversal:** Follow `INSTANTIATES` (reversed); follow `IMPLEMENTS` (reversed); follow `DERIVES_FROM` (reversed) one level  
**Filter:** Active and validated entities; exclude self-reported reuse and require independent, inspectable context
**Result shape:** List of reuse events with context  
**Use cases:** Evaluating Knowledge Gravity; assessing whether a pattern has sufficient reuse to promote; identifying where a principle is under-applied

**Required output fields:**
- each reuse event (entity identifier, type, reuse context — issue, PR, subsystem)
- reuse count per context type (governance, implementation, testing, verification)
- failed reuse attempts and their evidence
- total `reuse_count` from `knowledge_gravity.reuse_count`
- whether the count satisfies promotion thresholds in `knowledge_gravity.promotion_threshold`

---

### Q-007 — Historical Query

**Question:** What was the state of this entity at a specific point in time?

**Starting entity:** Any versioned entity  
**Traversal:** Follow `HAS_VERSION → VersionHistory`; select the version whose `effective_date ≤ target_date` and whose `superseded_by.effective_date > target_date` (or is null)  
**Filter:** Include superseded entities (this query is explicitly historical)  
**Result shape:** Single entity state at the requested time  
**Use cases:** Audit review; understanding what was true when a decision was made; incident post-mortems

**Required output fields:**
- entity identifier and canonical name at the time
- lifecycle state at the time
- governance status at the time
- all relationships active at the time
- version identifier

---

### Q-008 — Upward Compatibility Query

**Question:** Does this entity or proposed change contradict any Foundational Concept or constitutional article?

**Starting entity:** Any entity (typically an ArchitecturalPrinciple, Pattern, Artifact, System entity, or proposed change)
**Traversal:**  
1. Follow `DERIVES_FROM` upward to `FoundationalConcept` and `Constitution`.  
2. For each governing `FoundationalConcept`, check `CONTRADICTS` relationships targeting it.  
3. Check whether the entity's `relationships` include any explicit `CONTRADICTS` toward a Foundational Concept.  
**Filter:** Active and validated Foundational Concepts; active constitutional articles  
**Result shape:** List of (governing concept, relationship type, conflict status)  
**Use cases:** Pre-merge review; architecture review; TARP-0001 review process

**Required output fields:**
- for each Foundational Concept reached: the concept ID, the relationship chain, and whether
  a contradiction exists
- for the Constitution: the applicable articles and whether any are implicated
- overall compatibility verdict: `compatible`, `needs_review`, `explicit_conflict`
- if `explicit_conflict`: the evidence and the supersession requirement

---

### Q-009 — Full TARP Traceability Query

**Question:** Trace this implementation from its constitutional basis down to observable evidence.

**Starting entity:** CodeArtifact, ServiceComponent, ConfigurationArtifact, or ArchitectureDecisionRecord
**Traversal:**  
```
TRACES_TO → ArchitecturalPrinciple  
  → DERIVES_FROM → FoundationalConcept  
    → GOVERNS ← Constitution

IMPLEMENTS → ArchitectureDecisionRecord  
  → INFORMED_BY → Evidence (supporting the decision)  
  → VERIFIED_BY → VerificationRecord  
    → EVIDENCES → CI/test/review evidence
```
**Filter:** Active entities at each layer; include validated superseded entities for historical completeness  
**Result shape:** Directed graph from implementation to constitutional basis and back down through evidence  
**Use cases:** Architecture review; TARP-0001 review packets; audit; handoff between contributors

**Required output fields:**
- constitutional article(s) applicable
- Foundational Concept(s) applicable
- Architectural Principle(s) applicable
- Pattern(s) applied
- governing issue or decision record
- implementation artifact(s)
- verification evidence (CI runs, test results, review records)
- reopening conditions
- any broken links in the chain (registered as Risks per GI-011)

---

### Q-010 — Engineering Genome Query

**Question:** What is the current Engineering Genome, and what evidence supports each element?

**Starting entity:** AC-0002 (Engineering Genome Foundational Concept)  
**Traversal:** Follow `CONTRIBUTED_TO_GENOME` (reversed) to all genome members; for each member follow `knowledge_gravity.evidence_events` and `genome_membership.revision_history`  
**Filter:** Genome members with `membership_status = active`; optionally by `element_type`  
**Result shape:** List grouped by `element_type`  
**Use cases:** Onboarding new contributors; genome review; identifying gaps or conflicting elements

**Required output fields:**
- element identifier, type, and canonical name
- current `gravity_level`
- `member_since` date
- `membership_basis` (governance decision or review)
- most recent `evidence_refs` supporting membership
- `removal_conditions`

---

### Q-011 — Knowledge Gravity Review Query

**Question:** Has this knowledge gained or lost justified influence, and what is the overall distribution?

**Starting entity:** A knowledge entity, or none for a distribution review
**Traversal:** Read `knowledge_gravity` and traverse supporting evidence, reuse, contradiction, failure, staleness, and supersession events
**Filter:** Active and validated entities  
**Result shape:** Aggregation: count by `gravity_level`; list of entities at or above `pattern` level  
**Use cases:** Identifying high-authority knowledge; spotting knowledge entities overdue for review; governance health check

**Required output fields:**
- count of entities at each gravity level
- list of `foundational` and `principle`-level entities with last validation date
- list of entities with `review_due` in the past (overdue for review)
- factors increasing and decreasing influence, confidence, and unresolved uncertainty
- evidence-backed recommendation: `retain`, `promote`, `constrain`, `revalidate`, `demote`,
  `supersede`, `retire`, or `request_more_evidence`

---

### Q-012 — Candidate Promotion Query

**Question:** Has this Architectural Candidate earned an adopt, modify, or reject decision?

**Starting entity:** ArchitecturalCandidate
**Traversal:** Follow `APPLIED_IN`, `SUPPORTS`, `CONTRADICTS`, `DERIVES_FROM`, and `TRACES_TO`;
resolve constitutional and Foundational Concept compatibility
**Filter:** Independent applications only; all contradictory and failed application evidence;
then-effective versions under `as_of`
**Result shape:** Evidence graph plus recommendation

**Required output fields:**
- independent applications, reuse outcomes, benefits, costs, and failed applications
- supporting and contradicting evidence with provenance
- unresolved risks and constitutional or Foundational Concept conflicts
- current candidate status and promotion-gate completion
- recommendation and authority required; insufficient evidence returns `PARTIALLY_SUPPORTED` or
  `UNKNOWN`, never automatic promotion

---

## 4. Query Result States and Explanation

Every query returns one of `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `CONFLICT`,
`STALE`, `UNKNOWN`, or `NOT_APPLICABLE`. Confidence or ranking may supplement that state but may
not convert `UNKNOWN` or `CONFLICT` into a positive claim.

Every material result explains:

- entities and versions traversed;
- relationship types and directions used;
- temporal and authority boundaries;
- evidence included and excluded;
- unresolved contradictions and exact missing links; and
- the reason for the result state.

Opaque retrieval is insufficient for Governance, Verification, or Assurance decisions.

## 5. Query Result Quality Requirements

For any canonical query result to be usable as evidence or authoritative input:

1. The result must identify the entities, relationship types, and traversal path that produced it.
2. The result must note any broken links, missing evidence, or retired/excluded entities encountered.
3. The result must include a timestamp and the identity of the actor or system that ran it.
4. Results containing entities with `lifecycle_state = draft` must be flagged.
5. Results that would change if superseded entities were included must note this.

These requirements prevent a query result from being treated as authoritative when it reflects
an incomplete or inconsistent graph state.
