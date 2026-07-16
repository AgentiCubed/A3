# ACR-0001 — Architectural Candidate Register

## Purpose

This register preserves architectural concepts that require durable evaluation, promotion, supersession, or retirement. It provides a reviewable history for concepts that are more stable than implementation patterns but may still evolve through evidence.

## Governing Hierarchy

AgentiCubed currently uses the following architecture hierarchy:

1. Constitution
2. Foundational Concepts
3. Architectural Principles
4. Patterns
5. Implementations

No lower layer may contradict a higher layer without an explicit, evidence-backed supersession decision.

## Candidate Lifecycle

Architectural concepts move through the following lifecycle:

- **Proposed** — recorded for review but not yet adopted
- **Under Review** — actively being evaluated across architecture work
- **Adopted** — accepted for current use at a defined layer
- **Superseded** — replaced by a newer concept or formulation with explicit rationale
- **Retired** — preserved for history but no longer expected to guide current work

## Register

| ID | Concept | Current status | Layer | Source |
|---|---|---|---|---|
| **AC-0001** | Knowledge Gravity | Adopted | Foundational Concept | Issue #12 comments on 2026-07-16 |
| **AC-0002** | Engineering Genome | Adopted | Foundational Concept | Issue #12 comments on 2026-07-16 |
| **AC-0004** | Separation of Decision and Execution | Proposed | Foundational Candidate | Issue #12 comment on 2026-07-16 |

## AC-0001 — Knowledge Gravity

**Status:** Adopted  
**Layer:** Foundational Concept

Knowledge should gain or lose authority through accumulated evidence, validation, and successful reuse rather than age or author.

**Promotion / retention rule**
- continue applying it across memory, governance, verification, architecture, planning, and release work;
- strengthen its authority when repeated use improves decisions and reuse quality;
- preserve explicit traceability when a lower-level artifact depends on it.

**Supersession rule**
- may be superseded only by an explicit architectural review that states the conflict, presents stronger evidence, and preserves the prior concept's history.

## AC-0002 — Engineering Genome

**Status:** Adopted  
**Layer:** Foundational Concept

AgentiCubed should preserve its evolving engineering character: principles, patterns, anti-patterns, heuristics, governance rules, verification practices, architectural preferences, and risk tolerances.

**Promotion / retention rule**
- future subsystem and governance designs should explicitly state whether they enrich, weaken, or leave unchanged the Engineering Genome;
- durable records that capture reusable practice should be promoted into institutional memory when validated.

**Supersession rule**
- may be superseded only through an explicit review that explains why a different organizing model better preserves reusable engineering knowledge and governance continuity.

## AC-0004 — Separation of Decision and Execution

**Status:** Proposed  
**Layer:** Foundational Candidate

Decision authority and execution authority should remain distinct enough that implementation does not silently redefine product, governance, or verification decisions.

**Promotion rule**
- accumulate evidence through repeated, successful application across independent design phases and subsystems;
- require evidence that the concept improves architectural clarity, governance, verification, and subsystem separation before promotion to an adopted foundational concept or principle.

**Supersession rule**
- if later work finds a stronger formulation, preserve AC-0004 and link the successor rather than silently renaming or replacing it.

## Review Expectations

Future architecture phases should explicitly evaluate impacts on AC-0001 and AC-0002 and state whether AC-0004 is strengthened, weakened, promoted, or rejected.

Significant architectural decisions should use [TARP-0001 — Traceable Architecture Review Process](../playbook/TARP-0001-traceable-architecture-review-process.md) and link back to this register.
