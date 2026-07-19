# AgentiCubed Institutional Memory System

## Purpose

This system preserves more than outcomes. It records failures, interpretation, idea evolution, authority decisions, changed confidence, unexpected success, and reusable patterns so future human and autonomous contributors can reuse the search path rather than merely inherit its conclusion.

The durable learning unit is the traceable transition:

`prior model → disturbing evidence → revised model → tested consequence`

The system is subordinate to the AgentiCubed Constitution. It creates no constitutional authority.

## Canonical Memory Architecture

| Layer | Role | Includes | Excludes |
|---|---|---|---|
| **Working memory** | Ephemeral execution context used to complete the current task | live conversation, scratch notes, temporary shell output, unpublished hypotheses | any claim that must survive the session or justify future work on its own |
| **Project memory** | Durable, workstream-scoped context for a specific issue, PR, release, or subsystem | issue bodies, PR descriptions, task packets, ADRs, governance decisions, release evidence, issue-specific experiments | generalized lessons not yet validated beyond the workstream |
| **Institutional memory** | Stable, reusable knowledge intended to guide future contributors across workstreams | knowledge records, patterns, anti-patterns, risks, assumptions, experiments, architectural candidate register, traceability links | purely local implementation notes with no reuse value |
| **Evolution memory** | Preserved record of how beliefs, decisions, and authority changed over time | Idea Evolution Records, TET capsules, supersession chains, review triggers, confidence updates | silent rewrites that erase the prior state |

Working memory may inform durable records, but it is never the canonical repository of record.

Project memory is where a decision first becomes reviewable.

Institutional memory is where a validated lesson becomes reusable.

Evolution memory is not a separate silo. It is the rule that changes must preserve before-and-after state, disturbing evidence, and reopening conditions.

## Foundational Concepts and Governance Alignment

The institutional memory system shall preserve and strengthen the adopted Foundational Concepts recorded in [ACR-0001 — Architectural Candidate Register](./ACR-0001-architectural-candidate-register.md):

- **AC-0001 — Knowledge Gravity**
- **AC-0002 — Engineering Genome**

Knowledge Gravity governs promotion. Knowledge gains authority through verified evidence and successful reuse, not by author seniority or document age.

The Engineering Genome is the evolving set of principles, patterns, anti-patterns, heuristics, governance rules, verification practices, architectural preferences, and risk tolerances that describe how AgentiCubed engineers systems.

The [Upward Compatibility Rule](../playbook/STD-0002-traceable-architecture-reviews.md) applies throughout the architecture stack:

`Constitution → Foundational Concepts → Architectural Principles → Patterns → Implementations`

No lower layer may contradict a higher layer without explicit, evidence-backed supersession.

## Canonical Record Taxonomy

| Record | Use when | Do not use when | Identifier / location |
|---|---|---|---|
| **Failure Record (FR)** | an observed failure must be preserved as fact | you mainly need interpretation or a decision rationale | `FR-NNNN` in this directory |
| **Rumination (RM)** | a failure needs structured interpretation, competing hypotheses, or generalized heuristics | there is no linked factual failure record | `RM-NNNN` in this directory |
| **Idea Evolution Record (IER)** | an important idea changed across multiple stages and you must preserve the chronology | a single decision can be explained without stage history | `IER-NNNN` in this directory |
| **Reasoning Ledger (RL)** | a claim or decision needs explicit evidence, counter-evidence, confidence updates, and review triggers | you only need the final authority decision without the reasoning path | `RL-NNNN` in this directory |
| **Traceable Epistemic Transition capsule (TET)** | you need the smallest reusable capsule of belief change: prior model, disturbing evidence, revised model, tested consequence | the full surrounding record already makes the transition obvious and no reusable capsule is needed | `TET-NNNN` in this directory or embedded within another record |
| **Decision Record** | an authority decision must be ratified in its governing namespace | you are still exploring or only preserving evidence | Governance decisions in `docs/governance/decisions/`; architecture decisions in `docs/decisions/` |
| **Pattern** | repeated successful practice has enough evidence to recommend reuse | the behavior succeeded only once or is still hypothesis-level | `PAT-NNNN` in this directory |
| **Anti-pattern** | repeated harmful practice is identifiable and should be recognized early | the failure mode is isolated or not yet recurring | `AP-NNNN` in this directory |
| **Risk** | a material downside, trigger, or exposure needs owner, mitigation, and review conditions | the statement is only an unverified premise | `RSK-NNNN` in this directory |
| **Assumption** | work is proceeding on an unverified premise that must remain visible and testable | the premise has already been validated or rejected | `ASM-NNNN` in this directory |
| **Experiment** | an intentional test is being run to reduce uncertainty or compare options | the observation happened accidentally and was not designed as a test | `EXP-NNNN` in this directory |
| **Unexpected Success Record** | an outcome was materially better than expected and may reveal a reusable strength or overlooked mechanism | the success was predicted and already captured by normal verification | `USR-NNNN` in this directory |

### Anti-duplication rule

Do not create a new record type when an existing one already fits:

- use **RL** for decision reasoning, not a second decision log;
- use **Decision Records** for authoritative outcomes, not RLs alone;
- use **IER** when the sequence of change matters more than a single conclusion;
- use **TET** as a compact transition capsule, not as a replacement for FR, RM, IER, or RL;
- use **Pattern** and **Anti-pattern** only after more than one meaningful application or recurrence;
- use **Risk**, **Assumption**, and **Experiment** for live uncertainty management rather than hiding those elements inside prose.

## Lifecycle

### 1. Capture triggers

Create or update a durable record when any of the following occurs:

- a failure forces recovery, rollback, or repeated debugging;
- a design decision changes architecture, governance, verification, or release behavior;
- a belief changes because evidence contradicted the prior model;
- a pattern or anti-pattern repeats across independent tasks;
- a material risk, assumption, or experiment begins influencing delivery;
- a result is unexpectedly successful and may be reusable;
- a higher-layer concept, principle, or pattern is strengthened, weakened, introduced, retired, or superseded.

### 2. Classification

Classify in this order:

1. **What happened?** fact, interpretation, chronology, decision, risk, assumption, experiment, or surprising success
2. **What is the scope?** local workstream, cross-project, or project-wide governance
3. **What is the smallest sufficient record?** avoid splitting one event into many files without benefit
4. **Does an existing record need extension instead of a new file?** prefer linked updates over duplicates

### 3. Evidence requirements

Every durable record shall include enough evidence for a reviewer with no conversational memory to answer:

- what happened or was decided;
- which evidence supports it;
- which statements are facts, interpretations, hypotheses, and authority decisions;
- what changed as a result;
- what would reopen the matter.

Stable evidence may include repository paths, commit SHAs, issues, PRs, CI runs, logs, release tags, commands, measurements, screenshots, and linked records.

### 4. Validation states

Unless a record template defines a narrower operational status, the canonical validation lifecycle is:

`Draft → Active → Validated → Superseded | Retired`

- **Draft** — written but not yet reviewable or sufficiently evidenced
- **Active** — current working record; usable but still awaiting stronger evidence or reuse
- **Validated** — evidence or repeated reuse has increased confidence
- **Superseded** — replaced by a newer record that preserves the prior state and reason for change
- **Retired** — intentionally kept for history but no longer expected to guide current work

Type-specific states may exist inside the body, but they do not replace the validation lifecycle.

### 5. Stable identifiers and links

Use stable identifiers:

- `FR-NNNN`
- `RM-NNNN`
- `IER-NNNN`
- `RL-NNNN`
- `TET-NNNN`
- `PAT-NNNN`
- `AP-NNNN`
- `RSK-NNNN`
- `ASM-NNNN`
- `EXP-NNNN`
- `USR-NNNN`

Decision Records keep their existing namespaces:

- `DR-NNNN` for governance decisions
- `ADR-NNNN` for architecture decisions

Each record shall link to related issues, PRs, releases, decisions, evidence, and other knowledge records.

### 6. Promotion, review, and supersession

Knowledge promotion follows Knowledge Gravity:

| Promotion path | Minimum evidence expectation |
|---|---|
| Observation → Lesson | one verified event with a usable conclusion |
| Lesson → Pattern / Anti-pattern | repeated application or recurrence across independent work |
| Pattern → Principle | sustained successful reuse with bounded exceptions |
| Principle → Constitutional candidate or amendment input | repeated high-stability value plus governance review |

Supersession never deletes the earlier record. It adds:

- what changed;
- why it changed;
- which evidence changed it;
- which record now governs.

## Engineering Genome Maintenance

The Engineering Genome is updated when a Pattern, Anti-pattern, Risk tolerance, verification practice, governance rule, or architectural preference is introduced, strengthened, weakened, or retired.

The genome should evolve through validated experience rather than aspiration. A polished document with weak evidence has low Knowledge Gravity.

## Architectural Candidate Register

Foundational Concepts and other architecture-wide candidates shall be tracked in [ACR-0001 — Architectural Candidate Register](./ACR-0001-architectural-candidate-register.md).

Future architecture phases must explicitly evaluate the impact on:

- AC-0001 — Knowledge Gravity
- AC-0002 — Engineering Genome

and, where relevant, any later candidates in the register.

## Traceable Architecture Review

Significant architectural proposals shall follow [STD-0002 — Traceable Architecture Reviews](../playbook/STD-0002-traceable-architecture-reviews.md).

That standard operationalizes the required chain from higher-layer authority down to implementation and back up through verification and learning.

## Initial Record Set

The first worked example documents the Constitution v1.0 and Amendment A-0001 delivery:

- [FR-0001 — Constitutional release process failures](./FR-0001-constitutional-release-process.md)
- [RM-0001 — Why the release process required repeated recovery](./RM-0001-constitutional-release-process.md)
- [IER-0001 — Evolution of the constitutional baseline](./IER-0001-constitutional-baseline.md)
- [RL-0001 — Why failure-first institutional memory is required](./RL-0001-failure-first-memory.md)

The canonical Task 3 governance artifacts are:

- [DR-0002 — Institutional Memory System and Traceability](../decisions/DR-0002-Institutional-Memory-System-and-Traceability.md)
- [ACR-0001 — Architectural Candidate Register](./ACR-0001-architectural-candidate-register.md)
- [STD-0002 — Traceable Architecture Reviews](../playbook/STD-0002-traceable-architecture-reviews.md)

## Maintenance

Records are append-only where historical claims are concerned. Corrections must preserve the prior statement, the correction, the evidence, and the date of change.

Success is not measured by the number of records produced. A record is valuable only when it helps a later contributor deliver, verify, maintain, or safely change the product.
