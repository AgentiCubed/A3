# TARP-0001 — Traceability and Review Protocol

**Type:** Protocol (subordinate instrument)
**Status:** Proposed — reconstructed from issue-text usage; awaiting Principal
review and an explicit adoption decision
**Drafted by:** delegated agent (Executor); the drafter must not be the sole
reviewer (STD-0001)

## Provenance and unknowns

TARP-0001 is cited as the review and traceability mechanism across issues
#16, #17, and #19, with no defining artifact. This document reconstructs it
from:

- Issue #16 (Verification): "Review through TARP-0001: Constitution →
  Foundational Concepts → Ontology → Architectural Principles → Patterns →
  Implementations."
- Issue #16 (scope item 10): "alignment with TARP-0001 and the Upward
  Compatibility Rule."
- Issue #16 (required outputs): "TARP-0001 traceability mapping."
- Issue #19 (inputs): "TARP-0001."

**Recorded unknowns:**

1. The expansion of the acronym "TARP" is not recorded in any repository
   artifact or issue text. This document uses "Traceability and Review
   Protocol" as a working expansion; the Principal should confirm or correct
   it at review.
2. The **Upward Compatibility Rule** is cited alongside TARP-0001 (issue
   #16, scope 10) but defined nowhere. It is flagged here as a dangling
   reference requiring its own landing; this document does not invent its
   content. **[open item]**

## The chain

TARP-0001 fixes a six-layer chain of architectural authority and derivation:

```
1. Constitution            (ratified; supreme — Art. XI)
2. Foundational Concepts   (AC-0001, AC-0002, …)
3. Ontology                (issue #16 workstream)
4. Architectural Principles (adopted candidates — ARCHITECTURE-v2 §7)
5. Patterns                (recurring, evidenced solutions)
6. Implementations         (the shipped platform and future systems)
```

## Rules

1. **Downward derivation.** Every durable architectural statement at layer N
   must trace to authority at some layer above it. A pattern that traces to
   no principle, or a principle that traces to no concept or constitutional
   ground, is an orphan — a defect to resolve, not a curiosity.
2. **Upward protection.** No lower layer may contradict a higher layer; a
   conflict is resolved in the higher layer's favor or by explicitly
   changing the higher layer through its own procedure (Constitution
   Art. XI, Art. XII; candidate lifecycle for layers 2 and 4).
3. **Review follows the chain.** Reviewing an artifact under TARP-0001 means
   walking its trace: identify the layer, verify its upward links exist and
   still hold, and verify the artifact is context-complete for that walk
   (STD-0001). Issue #16's ontology work is itself reviewed this way.
4. **Traceability is explicit.** Links between layers are recorded
   relationships, not inferred resemblance — the same rule the ontology
   (#16) will formalize as its relationship vocabulary, and the reason
   candidate AC-0005 "Explicit Relationships" exists.
5. **Implementations are evidence, not authority.** Layer 6 feeds evidence
   upward (a pattern proven in the platform strengthens its principle's
   case) but never confers adoption downward-in-reverse
   (ARCHITECTURE-v2 §0.2, §7).

## Current state of the chain (at landing)

| Layer | State |
|-------|-------|
| 1 Constitution | Ratified (v1.0 + A-0001) |
| 2 Foundational Concepts | AC-0001, AC-0002 landed as proposals (this PR); AC-0003…0006 still unlanded |
| 3 Ontology | Open — issue #16 |
| 4 Architectural Principles | None adopted; lifecycle defined (ARCHITECTURE-v2 §7) |
| 5 Patterns | Not yet cataloged; platform seams are candidates-in-waiting |
| 6 Implementations | Shipped platform (backend/, frontend/) |

## Reopening conditions

- Issue #16 lands relationship semantics that change what "trace" means.
- The Upward Compatibility Rule lands and interacts with rules 1–2.
- The Principal corrects the acronym expansion or the chain's layers.

## Traceability

This protocol operationalizes Constitution Art. XI (supremacy) and
Art. VIII §4 (subordinate conflict resolution) for architectural artifacts;
it is itself a layer-4-adjacent subordinate instrument and holds authority
only while consistent with the Constitution and traceable to a Principal.
