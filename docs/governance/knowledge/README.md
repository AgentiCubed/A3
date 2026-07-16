# AgentiCubed Institutional Knowledge System

## Purpose

This system preserves more than outcomes. It records failures, interpretation, idea evolution, and the reasoning that changed decisions so future human and autonomous contributors can reuse the search path rather than merely inherit its conclusion.

The system is subordinate to the AgentiCubed Constitution. It creates no constitutional authority.

## Memory Architecture

AgentiCubed uses four memory layers. Each layer has a different boundary and promotion path.

| Layer | Purpose | Typical artifacts | Boundary |
|---|---|---|---|
| **Working memory** | Active, local problem-solving during a gate | chat context, scratch reasoning, temporary notes | Useful for execution but not durable authority; do not rely on it as the only source of evidence or review context |
| **Project memory** | Durable coordination state for a change stream | issues, PRs, review comments, CI logs, task packets, release notes | Durable but scoped to a project, branch, issue, or release; promote key learning before the workstream closes |
| **Institutional memory** | Canonical reusable knowledge for future contributors | reviewed governance docs, knowledge records, ratification artifacts | Reviewable, linkable, and stable enough to guide future work without conversational memory |
| **Evolution memory** | Preservation of how models, designs, and beliefs changed over time | IER, TET, architectural candidate history, supersession chains | Stores transitions, reversals, and reopening conditions so the project keeps change history instead of only current state |

A fact should move upward only when its evidence and reuse justify promotion. Lower layers may inform higher layers, but they do not gain authority automatically.

## Canonical Record Taxonomy

### Failure Record (FR)

A factual account of an observed failure.

A Failure Record separates:

- observed behavior;
- expected behavior;
- evidence;
- impact;
- immediate correction;
- verification;
- unresolved facts.

It does not assign blame, speculate about motive, or conceal responsibility.

### Rumination (RM)

A structured analysis linked to a Failure Record.

A Rumination examines:

- why the failure occurred;
- competing hypotheses;
- rejected explanations;
- system and human factors;
- deeper recurring patterns;
- updated mental models;
- future heuristics.

Interpretation must remain visibly distinct from verified fact.

### Idea Evolution Record (IER)

A chronological record of how an important idea changed.

An IER preserves:

- the initial formulation;
- assumptions at each stage;
- contradictions or failures encountered;
- evidence that caused revision;
- discarded branches;
- the current formulation;
- conditions that could reopen the decision.

### Reasoning Ledger (RL)

A decision-focused evidence ledger.

Every significant decision should record:

- Claim;
- Assumptions;
- Evidence;
- Counter-evidence;
- Alternatives considered;
- Why rejected;
- Confidence before;
- Confidence after;
- Trigger that changed confidence;
- Remaining uncertainty.

A Reasoning Ledger does not require certainty. It requires traceability.

### Traceable Epistemic Transition (TET)

A compact record of a belief change.

Use a TET when the key learning is the transition itself:

`prior model → disturbing evidence → revised model → tested consequence`

A TET is smaller than an IER and more explicit than scattered comments or commit messages.

### Pattern

A validated, reusable solution shape that has improved outcomes in more than one comparable situation.

Use a Pattern when the project has enough evidence to recommend repeating an approach under stated preconditions.

### Anti-pattern

A recurring solution shape that reliably produces avoidable harm, confusion, rework, or false confidence.

Use an Anti-pattern when repeated evidence shows an approach should be avoided or tightly bounded.

### Risk

A material uncertainty with a plausible path to product, governance, operational, or architectural harm.

Use a Risk record when a threat needs explicit ownership, monitoring, mitigation, or reopening criteria.

### Assumption

A premise accepted temporarily so work can proceed before full validation.

Use an Assumption record when a decision, design, or experiment depends on a claim that is not yet fully verified.

### Experiment

A bounded test intended to validate, weaken, or reject an assumption, design option, or risk mitigation.

Use an Experiment record when the project needs deliberate evidence rather than informal trial and error.

### Unexpected Success Record (USR)

A record of a positive outcome that was not predicted or not fully understood at the time it occurred.

Use a USR when the project would otherwise lose the conditions that produced an accidental or surprising win.

### Decision Records

Do not duplicate existing decision namespaces inside the knowledge system.

- Governance decisions belong under `docs/governance/decisions/`.
- Architectural decisions belong under `docs/decisions/`.

Knowledge records should link to the governing decision record instead of re-creating it in another template.

## Linking Rules

Each record uses a stable identifier:

- `FR-NNNN`
- `RM-NNNN`
- `IER-NNNN`
- `RL-NNNN`
- `TET-NNNN`
- `PAT-NNNN`
- `APAT-NNNN`
- `RSK-NNNN`
- `ASM-NNNN`
- `EXP-NNNN`
- `USR-NNNN`

Related records link to one another explicitly. A Failure Record may have multiple Ruminations. An Idea Evolution Record may reference several Failure Records and Reasoning Ledgers. Patterns, Anti-patterns, Risks, Assumptions, and Experiments should link back to the evidence, decisions, and releases that justify them.

## Capture Triggers

Create or update a durable record when any of the following occurs:

- a failure, recovery, or verification gap materially affects delivery, governance, or safety;
- evidence causes confidence to change in a claim or design choice;
- an idea changes enough that future contributors would need the discarded branch or reopening conditions;
- a reusable pattern or harmful anti-pattern appears across more than one task, PR, or release;
- a risk, assumption, or experiment becomes material to a design, release, or review decision;
- a surprising success occurs that should be reproducible rather than rediscovered;
- an architectural concept needs durable adoption, review, promotion, or supersession tracking;
- project memory is about to disappear unless distilled into an institutional artifact.

## Validation States

Every knowledge artifact should expose its validation state clearly.

| State | Meaning |
|---|---|
| **Captured** | Recorded with an identifier and minimum evidence, but not yet independently reviewed for reuse |
| **Reviewed** | Context-complete and checked for classification, evidence quality, and link integrity |
| **Validated** | Accepted for future reuse because evidence and review are sufficient for the intended scope |
| **Superseded** | Replaced by newer or stronger evidence; retained for history with an explicit successor link |
| **Retired** | Preserved for audit history but no longer expected to guide current work |

Record-specific status fields may add more detail, but they should map cleanly onto these states.

## Lifecycle and Supersession Rules

The institutional memory lifecycle is:

1. **Capture** the event, claim, or transition in working or project memory.
2. **Classify** it into the smallest durable record type that fits without duplication.
3. **Stabilize** the record with stable references, evidence, and explicit links.
4. **Review** it for context completeness, factual separation, and appropriate scope.
5. **Validate** it for reuse or keep it at a lower validation state if evidence remains incomplete.
6. **Promote, supersede, or retire** it as later evidence changes its authority.

Supersession rules:

- never silently overwrite a material historical claim;
- preserve the prior record and link the successor explicitly;
- state what changed, why it changed, and which evidence justified the change;
- record the effective date of the supersession;
- keep lower-layer artifacts from contradicting higher-layer artifacts without an explicit review or supersession decision.

## Context-Complete Review Rule

Every record must contain enough context for a reviewer to evaluate it without conversational memory.

A record fails review when a future contributor must ask:

- What happened?
- Which repository, branch, issue, PR, or release is involved?
- What evidence supports this claim?
- Which statements are facts and which are interpretations?
- What changed as a result?

## Foundational Concepts and System Integration

The knowledge system explicitly integrates the current foundational concepts adopted through Issue #12.

### Knowledge Gravity (AC-0001)

Knowledge gains or loses authority through evidence, validation, and successful reuse rather than age or author. Promotion should therefore be evidence-backed and reversible.

### Engineering Genome (AC-0002)

The repository should preserve its evolving engineering character: principles, patterns, anti-patterns, heuristics, governance rules, verification practices, architectural preferences, and risk tolerances. The knowledge system is the durable substrate for that genome.

### Integration consequences

- record validation state determines whether a claim is merely captured or reusable;
- patterns, anti-patterns, risks, and assumptions are first-class parts of the Engineering Genome;
- architectural concepts and their promotion path are tracked in the [Architectural Candidate Register](./ACR-0001-architectural-candidate-register.md);
- significant architectural changes should use [TARP-0001 — Traceable Architecture Review Process](../playbook/TARP-0001-traceable-architecture-review-process.md).

## Knowledge Transmission Principle

Knowledge does not automatically become more valuable each time it changes hands.

Transmission adds value only when it improves at least one of:

- discoverability;
- context;
- validation;
- applicability;
- correction;
- connection to other knowledge;
- resilience against loss.

Repeated transmission without those controls can reduce value through distortion, context collapse, stale assumptions, or false consensus.

See [Knowledge Transmission and Compounding Value](./knowledge-transmission.md).

## Reference Artifacts

- [Institutional Knowledge Record Templates](./templates.md)
- [Architectural Candidate Register](./ACR-0001-architectural-candidate-register.md)
- [Knowledge Transmission and Compounding Value](./knowledge-transmission.md)
- [TARP-0001 — Traceable Architecture Review Process](../playbook/TARP-0001-traceable-architecture-review-process.md)

## Initial Record Set

The first worked example documents the Constitution v1.0 and Amendment A-0001 delivery:

- [FR-0001 — Constitutional release process failures](./FR-0001-constitutional-release-process.md)
- [RM-0001 — Why the release process required repeated recovery](./RM-0001-constitutional-release-process.md)
- [IER-0001 — Evolution of the constitutional baseline](./IER-0001-constitutional-baseline.md)
- [RL-0001 — Why failure-first institutional memory is required](./RL-0001-failure-first-memory.md)

## Maintenance

Records are append-only where historical claims are concerned. Corrections must preserve the prior statement, the correction, the evidence, and the date of change.

Success is not measured by the number of records produced. A record is valuable only when it helps a later contributor deliver, verify, maintain, or safely change the product.
