# ONTO-0004 — Knowledge Gravity and Engineering Genome

**Status:** Draft  
**Governing issue:** [#16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16)  
**Governing Foundational Concepts:** AC-0001 Knowledge Gravity, AC-0002 Engineering Genome  
**Layer:** Ontology (below Foundational Concepts; above Architectural Principles)

---

## 1. Knowledge Gravity

### 1.1 Governing Principle

**AC-0001 — Knowledge Gravity:** Knowledge gains or loses justified weight through accumulated
evidence and successful reuse rather than age or author. The Ontology must make this principle
operational: every entity to which Knowledge Gravity applies must carry metadata sufficient to
evaluate its current justified weight from inspectable evidence alone. Per
AC-0001 Rule 2 (adopted, DR-0004 P-1): gravity is not authority and never
outranks a Delegation, an acceptance condition, or a Principal decision.

Knowledge Gravity is not an arbitrary score. Every change to it must be traceable to a specific
event: evidence arrived, reuse occurred, contradiction was recorded, or supersession happened.

### 1.2 KnowledgeGravityMetadata Record

Required for the entity types named in the **authoritative list** in
ONTO-0001 §3 (Entity Family Summary): `Pattern`, `AntiPattern`,
`FoundationalConcept`, `ArchitecturalCandidate`, `ArchitecturalPrinciple`,
`ArchitecturalContract`.

| Field | Type | Description |
|---|---|---|
| `gravity_level` | GravityLevel | Current justified-weight level: `observation`, `lesson`, `pattern`, `principle`, `foundational`. |
| `evidence_events` | []GravityEvent | Ordered list of events that caused gravity to increase or decrease. |
| `positive_evidence_count` | Integer | Count of supporting evidence items since last validation. |
| `reuse_count` | Integer | Count of distinct reuse events (independent tasks, subsystems, phases). |
| `contradiction_count` | Integer | Count of recorded `CONTRADICTS` relationships against this entity. |
| `supersession_count` | Integer | Count of times this entity has superseded a prior entity. |
| `last_validated_at` | Timestamp | When the gravity level was last reviewed against current evidence. |
| `promotion_threshold` | PromotionThreshold | The evidence criteria required to promote to the next level. |
| `demotion_trigger` | DemotionTrigger | The evidence condition that would cause a gravity-level demotion. |
| `current_reviewer` | ActorReference | The entity responsible for the next scheduled gravity review. |
| `review_due` | Date | When the next gravity review is due. |

### 1.3 Gravity Levels

| Level | Meaning | Minimum evidence required |
|---|---|---|
| `observation` | A single verified event with a usable conclusion. | One confirmed event; no replication required. |
| `lesson` | An interpretation with supporting evidence. | At least one confirmed event with structured interpretation (RL, RM, or IER). |
| `pattern` | A repeated successful practice worth recommending. | Two or more independent application or recurrence events in different tasks or contexts. |
| `principle` | Sustained successful reuse with bounded exceptions. | Pattern-level evidence; exceptions explicitly bounded; applies across multiple subsystems. |
| `foundational` | Highest non-constitutional governance weight; project-wide. | Principle-level evidence; explicitly adopted by Principal; recorded in governance decision. |

Gravity levels form a strict hierarchy. Promotion skipping a level is not permitted. Promotion
from `pattern` to `foundational` in one step requires explicit Principal ratification and
extraordinary evidence.

### 1.4 GravityEvent Record

A `GravityEvent` records every cause of a gravity change.

| Field | Description |
|---|---|
| `event_type` | `evidence_added`, `reuse_recorded`, `contradiction_recorded`, `supersession_occurred` — the four bounded sources of AC-0001 Rule 1 (adopted as amended, DR-0004 P-1). Reviews, promotions, and demotions are governed **outcomes** recorded via `review_outcome`/level fields on an event from one of the four sources, never source event types of their own. |
| `review_outcome` | Optional; present when a governed review acted on this event: one of the ONTO-0004 §1.8 outcomes, with `authority_basis`. |
| `occurred_at` | Timestamp |
| `triggered_by` | Reference to the evidence entity, reuse record, or governance decision causing the change |
| `prior_gravity_level` | Gravity level before this event |
| `new_gravity_level` | Gravity level after this event (may be unchanged if only count updated) |
| `notes` | Optional explanation for the event |

### 1.5 Promotion Rules

| Promotion path | Required GravityEvents | Authority required |
|---|---|---|
| `observation` → `lesson` | One `evidence_added` carrying a confirming `review_outcome` | Any authorized reviewer |
| `lesson` → `pattern` | Two or more `reuse_recorded` events from independent contexts | Authorized reviewer; documented in a knowledge record |
| `pattern` → `principle` | Multiple `reuse_recorded` events across subsystems; exceptions explicitly bounded | Governance decision or authorized architecture review |
| `principle` → `foundational` | Sustained application across the project; prior Principal approval | Explicit Principal ratification; governance decision record |

### 1.6 Demotion Rules

Gravity is reduced when:

- a `CONTRADICTS` relationship records evidence that weakens the prior claim;
- an `Experiment` result disconfirms the knowledge entity's core claim;
- a `FailureRecord` attributable to applying the entity is created;
- a significant exception is identified that the principle's scope cannot accommodate.

Demotion does not erase the prior gravity level or its history. The `evidence_events` list
preserves the full chronology.

### 1.7 Anti-Gaming Safeguard

To prevent Knowledge Gravity from becoming arbitrary scoring theater:

- Only events with `evidence_refs` referencing inspectable, external evidence may change
  `positive_evidence_count` or `reuse_count`.
- Self-reported reuse (an entity citing itself) does not increment `reuse_count`.
- A Principal may audit the gravity record and flag it for review if the `evidence_events`
  list contains events without inspectable evidence.
- A `gravity_level` of `foundational` requires a governance decision record as authority; it
  may not be reached by evidence accumulation alone.

### 1.8 Governed Review Protocol

A gravity review is triggered by a new Architectural Candidate, a validated major
implementation, contradictory evidence, constitutional amendment, quarterly governance review,
or release retrospective. It considers evidence quality and independence, successful and failed
reuse, predictive performance, contradictions, staleness, supersession, scope breadth, and
authority status.

The review records an evidence-backed rationale and one outcome: `retain`, `increase_weight`,
`decrease_weight`, `promote`, `supersede`, `retire`, or `request_more_evidence`. **This is the
owning enumeration for gravity-review outcomes** (ONTO-0003 §8); ONTO-0005 Q-011 references
it — its former extra tokens map here as `constrain`/`revalidate` ↦ `retain` with recorded
conditions, `demote` ↦ `decrease_weight`. Numeric indicators may inform review but are never
the authoritative result.

Promotion of an `ArchitecturalCandidate` to `FoundationalConcept` requires all of:

1. successful application across at least three independent architectural workstreams;
2. no unresolved constitutional conflict;
3. a positive TARP-0001 traceability review;
4. demonstrated improvement in clarity, governance, or engineering quality; and
5. explicit governance approval.

---

## 2. Engineering Genome

### 2.1 Governing Principle

**AC-0002 — Engineering Genome:** AgentiCubed maintains an explicit, evolving genome of an
engineering organization consisting of principles, patterns, anti-patterns, heuristics,
governance rules, verification practices, architectural preferences, and risk tolerances.
The genome represents the organization's engineering character and evolves through validated
experience.

The Ontology makes genome membership explicit, versioned, and reversible. An entity is in
the genome only when its membership is recorded; membership is not inferred from content or
Knowledge Gravity level alone.

### 2.2 Genome Element Types

| Element type | Example | Typically contributes from |
|---|---|---|
| `principle` | Provider-neutral adapters; separation of execution and evaluation | `ArchitecturalPrinciple` with principle-level gravity |
| `pattern` | Gate workflow; failure-first institutional memory | `Pattern` with pattern-level gravity |
| `anti_pattern` | Self-expanding delegation; silent supersession | `AntiPattern` with pattern-level gravity |
| `heuristic` | If authority is ambiguous, Halt rather than infer | `RL`, `RM`, or `TETCapsule` |
| `governance_rule` | Executor shall not be sole Evaluator | `GovernanceDecision` or `ArchitecturalContract` |
| `verification_practice` | JSON field assertion over raw string matching for /readyz | `Pattern` or `ArchitecturalPrinciple` |
| `architectural_preference` | Temporal can replace Celery without touching domain logic | `ArchitectureDecisionRecord` with `DERIVES_FROM` |
| `risk_tolerance` | Tolerant CI teardown accepted over strict exit-code enforcement | `GovernanceDecision` backed by `Risk` entity |

### 2.3 GenomeMembershipRecord

Required for: entities explicitly designated as genome members.

| Field | Type | Description |
|---|---|---|
| `element_type` | GenomeElementType | One of the types above. |
| `member_since` | Date | When this entity joined the genome. |
| `membership_basis` | GovernanceReference | The decision or review that approved membership. |
| `membership_evidence` | []EvidenceReference | Evidence confirming this entity's genome suitability. |
| `revision_history` | []GenomeMembershipRevision | Ordered record of all changes to membership status. |
| `membership_status` | `active`, `under_review`, `suspended`, `removed` | Current standing. |
| `removal_conditions` | String | The conditions under which this element would be removed. |

### 2.4 Genome Membership Lifecycle

| Transition | Trigger | Authority required |
|---|---|---|
| Added to genome | Sufficient Knowledge Gravity + governance decision | Authorized architecture review or Principal |
| Placed under review | Contradicting evidence or application failure | Any contributor; escalates to reviewer |
| Suspended | Unresolved contradiction or active review | Reviewer or Principal |
| Removed | Evidence shows the element is harmful or obsolete | Governance decision; prior content preserved |
| Reinstated | Counter-evidence to removal is validated | Governance decision |

Removal is reversible. A removed genome element's `revision_history` preserves the full
sequence including the removal event, its evidence, and any reinstatement.

Genome evidence matures independently through:

```
proposed → observed → validated → incorporated → characteristic → foundational
                                              ↘ superseded | retired
```

`membership_status` records whether the element is currently in the genome; this maturity stage
records the strength and breadth of evidence. `foundational` maturity still requires governance
approval and cannot be inferred from a single successful use. Every promotion, retirement, or
reinstatement records TARP traceability, evidence links, rationale, and learned lessons.

### 2.5 Genome Revision Record

Each entry in `revision_history`:

| Field | Description |
|---|---|
| `revision_date` | When the revision occurred. |
| `prior_status` | Membership status before this revision. |
| `new_status` | Membership status after this revision. |
| `changed_by` | Actor who made the change. |
| `authority_basis` | Governance decision or review that authorized the change. |
| `evidence_refs` | Evidence that caused the change. |
| `notes` | Optional explanation. |

### 2.6 Genome Integrity Rules

- The genome is not a static document; it evolves through recorded, evidence-backed events.
- Membership must be explicit; no entity is in the genome by implication or proximity.
- A genome membership revision with no `authority_basis` or `evidence_refs` is a model
  violation.
- The genome's current state is derivable by replaying all `revision_history` entries from
  the initial membership record to the present.
- Genome membership status does not by itself change an entity's Knowledge Gravity level, and
  Knowledge Gravity level does not by itself change genome membership status. Both are
  governed independently.

---

## 3. Interaction Between Knowledge Gravity and the Engineering Genome

Knowledge Gravity governs how authoritative a knowledge entity is based on evidence and reuse.
The Engineering Genome governs which entities are explicitly designated as part of
AgentiCubed's engineering character.

These two systems interact:

| Scenario | Effect |
|---|---|
| An entity reaches `pattern` gravity | It becomes eligible for genome consideration, not automatically admitted. |
| A genome element's gravity falls (contradiction, failure) | Membership must be placed under review. |
| A genome element is removed | Its Knowledge Gravity history is preserved; the removal is recorded as a `GravityEvent`. |
| A Principal promotes an entity to `foundational` | It is also a candidate for genome membership at the `principle` or `governance_rule` level, pending separate decision. |

An entity in both systems carries both `knowledge_gravity` and `genome_membership` fields.
Neither field governs the other.
