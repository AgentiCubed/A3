# Agentic³ Ontology

## Purpose and Hierarchy Placement

The Agentic³ Ontology defines the canonical entity taxonomy, semantic relationships, lifecycle
rules, graph integrity constraints, and query semantics shared by all Agentic³ engines: Memory,
Knowledge, Governance, Verification, Assurance, and Evolution.

The Ontology occupies the third layer in the governing hierarchy:

```
Constitution → Foundational Concepts → Ontology → Architectural Principles → Architectural Contracts → Patterns → Implementations
```

The Ontology defines *what kinds of things exist* and *how they relate*. It does not confer
authority. Authority is governed by the Constitution and expressed through explicit governance
relationships.

## What the Ontology Governs

1. the root entity model and entity families;
2. the controlled relationship vocabulary;
3. graph integrity rules;
4. lifecycle, versioning, provenance, and identity semantics;
5. Knowledge Gravity metadata and update rules;
6. Engineering Genome membership and evolution rules;
7. query semantics for retrieval, provenance, impact, and contradiction analysis;
8. alignment with TARP-0001 and the Upward Compatibility Rule;
9. candidate evaluation for AC-0005 and AC-0006.

## What the Ontology Does Not Govern

- database selection or graph database implementation;
- API design or product features;
- Constitution changes;
- automatic promotion of architectural candidates;
- replacement of existing record types (FR, RM, IER, RL, TET, ADR, issue, PR, or release records).

## Documents

| Document | Contents |
|---|---|
| [ONTO-0001 — Entity Model](./ONTO-0001-entity-model.md) | Root entity model and all eight entity families |
| [ONTO-0002 — Relationship Vocabulary](./ONTO-0002-relationships.md) | Controlled relationships with source/target constraints and cardinality |
| [ONTO-0003 — Integrity and Lifecycle](./ONTO-0003-integrity-lifecycle.md) | Graph integrity rules, lifecycle states, versioning, provenance, identity |
| [ONTO-0004 — Knowledge and Genome](./ONTO-0004-knowledge-genome.md) | Knowledge Gravity metadata and Engineering Genome membership rules |
| [ONTO-0005 — Query Semantics](./ONTO-0005-query-semantics.md) | Query model for provenance, impact, contradiction, authority, and reuse |
| [ONTO-0006 — Candidates and Traceability](./ONTO-0006-candidates-traceability.md) | AC-0005/AC-0006 evaluation, TARP-0001 traceability mapping, open risks |

## Governing Foundational Concepts

The Ontology is subordinate to two adopted Foundational Concepts (approved in
[Issue #12](https://github.com/AgentiCubed/agenticubed/issues/12)):

**AC-0001 — Knowledge Gravity**
Knowledge gains authority through verified evidence and successful reuse, not author seniority or
document age. The Ontology must preserve Knowledge Gravity metadata on the appropriate entity
types and support evidence-based promotion and demotion.

**AC-0002 — Engineering Genome**
AgentiCubed maintains an explicit, evolving genome of principles, patterns, anti-patterns,
heuristics, governance rules, verification practices, architectural preferences, and risk
tolerances. The Ontology must define how genome membership is explicit, versioned, and
reversible.

**Upward Compatibility Rule:** No Architectural Principle, Pattern, Implementation, or subsystem
derived from this Ontology may contradict a Foundational Concept without an explicit,
evidence-backed supersession decision.

## Governing Issue

This Ontology was designed under
[Issue #16 — Design the Agentic³ ontology and semantic graph](https://github.com/AgentiCubed/agenticubed/issues/16).

This is a specification workstream. No implementation is authorized by this document.
