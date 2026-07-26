# TARP-0001 — Traceability and Review Protocol

**Type:** Protocol (subordinate instrument)
**Status:** **Adopted** — by explicit Principal decision
[DR-0004](../governance/decisions/DR-0004-Phase-0-Reconciliation-Decisions.md)
P-4 (2026-07-26): this protocol is the traceability discipline that the
Active standard STD-0002 implements
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

Label legend: **[supported: …]** restates cited issue text;
**[reconstructed]** is inferred and correctable at review; **[proposed]** is
a new decision with no force until the Principal adopts it.

## Rules

1. **Downward derivation** **[reconstructed]**, with a **[proposed]** edge.
   Every durable architectural statement at layer N must trace to authority
   at some layer above it — inferred from #16's use of the chain for review
   and its acceptance criterion that "every durable architectural statement
   can be traced through explicit relationships." The classification of an
   untraceable statement as a **defect to resolve** (an "orphan") is a new
   proposed rule, not #16 text.
2. **Upward protection** **[reconstructed]**. No lower layer may contradict
   a higher layer; conflicts resolve in the higher layer's favor or by
   changing the higher layer through its own procedure. Inferred from
   Constitution Art. XI (supremacy) and Art. XII (amendment) extended down
   the chain — the extension below the constitutional layer is the
   inference.
3. **Review follows the chain** **[supported: #16 Verification]** in its
   core — #16 states "Review through TARP-0001: Constitution → … →
   Implementations." The tie-in to STD-0001 context-complete review is
   **[reconstructed]**.
4. **Traceability is explicit** **[reconstructed]**. Links between layers
   are recorded relationships, not inferred resemblance — drawn from #16's
   acceptance criteria and relationship-vocabulary scope. Note: this rule
   parallels candidate AC-0005 "Explicit Relationships," which is
   **undecided**; this protocol must not be read as pre-adopting AC-0005,
   and if AC-0005 is rejected this rule reopens.
5. **Implementations are evidence, not authority** **[reconstructed]** from
   ARCHITECTURE-v2 §0.2/§7 (themselves merged draft, not ratified doctrine).
   Layer 6 feeds evidence upward but never confers adoption in reverse.

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
