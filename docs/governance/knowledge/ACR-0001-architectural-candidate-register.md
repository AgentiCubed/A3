# ACR-0001 — Architectural Candidate Register

## Purpose

This register preserves architecture-wide concepts whose status, scope, and review history must remain explicit.

It exists so candidate concepts are neither silently discarded nor silently treated as settled doctrine.

## Lifecycle

Candidates move through this lifecycle:

`Proposed → Under Review → Adopted → Superseded → Retired`

- **Proposed** — introduced and protected from silent loss
- **Under Review** — actively being evaluated across architecture work
- **Adopted** — approved for project use within the stated scope
- **Superseded** — replaced by a better-supported candidate or concept
- **Retired** — preserved historically but no longer expected to guide design

Adopted candidates that govern the entire project may also be designated as **Foundational Concepts**.

## Upward Compatibility Rule

No Architectural Principle, Pattern, Implementation, or subsystem may contradict an adopted Foundational Concept without an explicit supersession decision supported by evidence.

## Register

| ID | Title | Current layer | Status | Summary | Evidence / source | Reopening or promotion conditions |
|---|---|---|---|---|---|---|
| **AC-0001** | Knowledge Gravity | Foundational Concept | Adopted | Knowledge gains or loses authority through accumulated evidence and successful reuse rather than age or author. | Issue #12 owner comments approving Foundational Concepts and upward compatibility on 2026-07-16. | Continue validating across governance, memory, verification, planning, orchestration, and release work; derive narrower Architectural Principles as evidence accumulates. |
| **AC-0002** | Engineering Genome | Foundational Concept | Adopted | AgentiCubed maintains an explicit, evolving genome of principles, patterns, anti-patterns, heuristics, governance rules, verification practices, architectural preferences, and risk tolerances. | Issue #12 owner comments approving Foundational Concepts and institutionalization on 2026-07-16. | Continue validating across subsystem designs; update whenever validated experience strengthens, weakens, introduces, or retires a genome element. |
| **AC-0004** | Separation of Decision and Execution | Foundational Candidate | Proposed | Decision authority and execution behavior should remain separable enough to reason about governance, verification, and subsystem boundaries independently. The title and promotion policy are preserved; fuller articulation remains pending. | Issue #12 owner comment adding AC-0004 as a Foundational Candidate on 2026-07-16. | Promotion requires repeated successful application across independent design phases and evidence that it improves clarity, governance, verification, and subsystem separation. |

## Review Requirement

Every future subsystem specification, ADR, architecture phase, and governance proposal that materially affects architecture shall explicitly evaluate its impact on AC-0001 and AC-0002.

Proposals materially affecting decision authority, delegation, or subsystem separation should also evaluate AC-0004.

## Historical Continuity

When a candidate changes status:

1. preserve the prior entry;
2. add the date and reason for the change;
3. link the governing issue, decision record, or ADR;
4. state what evidence caused the update.
