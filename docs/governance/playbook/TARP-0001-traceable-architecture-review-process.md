# TARP-0001 — Traceable Architecture Review Process

**Type:** Procedure  
**Version:** 1.0  
**Authority:** [POL-0001 Gate Workflow](./POL-0001-gate-workflow.md), [STD-0001 Context-Complete Reviews](./STD-0001-context-complete-reviews.md)  
**Status:** Active

---

## Purpose

This Procedure ensures every significant architectural decision leaves behind a reviewable chain of reasoning from implementation back through Patterns, Architectural Principles, Foundational Concepts, and the Constitution.

---

## Governing Hierarchy

Architectural review uses the following hierarchy:

1. Constitution
2. Foundational Concepts
3. Architectural Principles
4. Patterns
5. Implementations

No lower layer may contradict a higher layer without an explicit, evidence-backed supersession decision.

The current foundational concepts are tracked in the [Architectural Candidate Register](../knowledge/ACR-0001-architectural-candidate-register.md).

---

## Trigger

TARP-0001 is required for any proposal that materially affects one or more of:

- system boundaries;
- authority or delegation;
- data ownership or persistence;
- security or privacy posture;
- reliability or release behavior;
- cross-project standards;
- canonical workflows;
- memory architecture;
- Foundational Concepts;
- Architectural Principles;
- established Patterns;
- irreversible or difficult-to-reverse implementation choices.

Routine mechanical changes may use a lighter review unless they introduce one of the effects above.

---

## Required Review Packet

Every significant architectural proposal must include:

1. **Decision statement** — the exact choice under review.
2. **Context and problem** — what condition requires a decision.
3. **Evidence** — verified facts, measurements, incidents, experiments, and stable references.
4. **Assumptions and unknowns** — premises not yet verified.
5. **Alternatives considered** — viable options, including the status quo.
6. **Constitutional alignment** — applicable authority, rights, obligations, or an explicit statement that no constitutional provision is implicated.
7. **Foundational Concept alignment** — impact on AC-0001 Knowledge Gravity, AC-0002 Engineering Genome, and any future foundational concepts.
8. **Architectural Principle alignment** — principles reinforced, weakened, or intentionally superseded.
9. **Pattern alignment** — patterns applied, violated, introduced, or retired.
10. **Implementation mapping** — how the chosen implementation realizes the higher-layer reasoning.
11. **Consequences and risks** — expected benefits, costs, failure modes, and rollback difficulty.
12. **Verification plan** — observable evidence that will show whether the decision worked.
13. **Reopening conditions** — evidence or changed conditions that require reconsideration.
14. **Traceability links** — issue, ADR or decision record, PR, tests, CI, release, and related knowledge records.

---

## Review Sequence

Reviewers evaluate the proposal in this order:

1. **Constitutional compatibility**
   - Does the proposal respect authority, rights, evidence duties, delegation limits, and amendment requirements?
   - A conflict is a hard stop unless the proposal explicitly invokes the constitutional amendment process.

2. **Foundational Concept compatibility**
   - Does it strengthen or weaken Knowledge Gravity?
   - Does it enrich or erode the Engineering Genome?
   - Does it conflict with another Foundational Concept?
   - A conflict requires redesign or an explicit supersession proposal supported by evidence.

3. **Architectural Principle compatibility**
   - Is the decision consistent with adopted design principles?
   - Are exceptions explicit, bounded, and reviewable?

4. **Pattern compatibility**
   - Does the proposal apply established patterns correctly?
   - Is a new pattern being proposed from sufficient evidence?
   - Is an existing pattern being retired or narrowed?

5. **Implementation fidelity**
   - Is the implementation the smallest faithful realization of the approved reasoning?
   - Does the diff introduce contradictions, hidden scope, or accidental policy?

6. **Verification and learning**
   - Are success, failure, and reversal observable?
   - Which knowledge records will be created or updated after implementation?

---

## Required Decision Outcomes

A review must conclude with one of:

- **APPROVED** — fully aligned and sufficiently evidenced.
- **APPROVED WITH CONDITIONS** — acceptable after named conditions are satisfied.
- **REVISE** — may proceed only after specified conflicts or evidence gaps are corrected.
- **REJECTED** — incompatible with governing layers or unjustified by evidence.
- **DEFERRED** — insufficient information; specific experiment or evidence is required.
- **SUPERSESSION REQUIRED** — conflicts with a higher layer and may proceed only through an explicit supersession or amendment process.

---

## Required Traceability Chain

For an approved significant decision, the durable chain should be:

`Constitutional basis → Foundational Concept alignment → Architectural Principle → Pattern → Decision/ADR → Issue → PR/diff → Verification evidence → Release → Learning record`

Not every link requires a separate file, but every applicable link must be explicit and navigable.

---

## Post-Implementation Review

After implementation and verification:

- compare predicted consequences with observed results;
- record unexpected failures and successes;
- update Knowledge Gravity based on validation and reuse;
- update the Engineering Genome when a pattern, anti-pattern, heuristic, or principle is strengthened, weakened, introduced, or retired;
- create or update FR, RM, IER, RL, TET, Pattern, Anti-pattern, Risk, Assumption, Experiment, or USR records as appropriate;
- preserve the original decision and add corrections rather than silently rewriting history.

---

## Minimum PR Application

Every PR implementing a significant architectural decision should include an **Architecture Traceability** section containing:

- governing issue or decision record;
- constitutional alignment;
- Foundational Concept alignment;
- principles and patterns applied;
- implementation-to-rationale mapping;
- verification evidence;
- reopening conditions or follow-up review trigger.

---

## Acceptance Test

A future reviewer with no conversational memory must be able to answer:

- What was decided?
- Why was it necessary?
- Which evidence supported it?
- Which higher-layer concepts authorized or constrained it?
- How did the implementation realize the decision?
- How was success verified?
- What would cause the decision to be reconsidered?

If any answer requires reconstructing private conversation, the review record is incomplete.
