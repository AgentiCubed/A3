# DR-0002 — Institutional Memory System and Traceability

## Purpose

This Decision Record establishes the canonical AgentiCubed institutional memory system for architecture, governance, and engineering work.

It replaces the earlier four-record system as a narrow experiment with a broader, durable memory architecture that preserves failures, reasoning, evolving beliefs, risks, assumptions, experiments, patterns, and unexpected successes as reviewable repository artifacts.

## Context

AgenticCubed design work has been progressing conversationally. Conversation is effective working memory but not durable engineering memory.

Without a formal repository-backed system, the project risks:

- repeating resolved mistakes;
- rediscovering successful patterns;
- losing why decisions changed;
- inheriting conclusions without assumptions or counter-evidence;
- confusing facts, interpretations, hypotheses, decisions, and unknowns;
- creating documentation that is written but not reused.

Issue #12 and its owner-approved comments also introduced project-wide concepts and rules that needed durable preservation:

- AC-0001 — Knowledge Gravity
- AC-0002 — Engineering Genome
- AC-0004 — Separation of Decision and Execution
- the Upward Compatibility Rule
- TARP-0001 — Traceable Architecture Review Process

## Decision

AgentiCubed adopts the following as the canonical institutional memory system:

1. **Memory architecture** shall distinguish working memory, project memory, institutional memory, and evolution memory.
2. **Knowledge record taxonomy** shall include FR, RM, IER, RL, TET, Pattern, Anti-pattern, Risk, Assumption, Experiment, and Unexpected Success Record, with existing Decision Record namespaces retained rather than duplicated.
3. **Knowledge Gravity** and the **Engineering Genome** are integrated into the memory system as adopted Foundational Concepts tracked in an Architectural Candidate Register.
4. **TARP-0001** is adopted as the standard review process for significant architectural proposals.
5. Durable architecture-wide candidates shall be tracked in an explicit register with lifecycle `Proposed → Under Review → Adopted → Superseded → Retired`.

The normative specification is recorded in:

- [Institutional Memory System](../knowledge/README.md)
- [Institutional Knowledge Record Templates](../knowledge/templates.md)
- [ACR-0001 — Architectural Candidate Register](../knowledge/ACR-0001-architectural-candidate-register.md)
- [STD-0002 — Traceable Architecture Reviews](../playbook/STD-0002-traceable-architecture-reviews.md)

## Consequences

### Positive

- Future contributors can reconstruct what changed, why it changed, and what evidence caused the change.
- Foundational Concepts are preserved as explicit review constraints rather than implicit owner memory.
- Architectural review becomes traceable from governing authority down to implementation and back through verification.
- Reusable knowledge can accumulate authority through evidence and successful reuse.

### Costs

- Contributors must classify records carefully and maintain links.
- More repository artifacts will exist, so poor curation could create noise.
- Review discipline is required to prevent records from becoming polished but weakly evidenced prose.

## Authority and scope

This Decision Record is subordinate to the AgentiCubed Constitution and applies to governance, architecture, verification, planning, orchestration, release management, and future constitutional evolution work performed in this repository.
