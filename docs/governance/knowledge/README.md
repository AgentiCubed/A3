# AgentiCubed Institutional Knowledge System

## Purpose

This system preserves more than outcomes. It records failures, interpretation, idea evolution, and the reasoning that changed decisions so future human and autonomous contributors can reuse the search path rather than merely inherit its conclusion.

The system is subordinate to the AgentiCubed Constitution. It creates no constitutional authority.

## Record Types

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

## Linking Rules

Each record uses a stable identifier:

- `FR-NNNN`
- `RM-NNNN`
- `IER-NNNN`
- `RL-NNNN`

Related records link to one another explicitly. A Failure Record may have multiple Ruminations. An Idea Evolution Record may reference several Failure Records and Reasoning Ledgers.

## Context-Complete Review Rule

Every record must contain enough context for a reviewer to evaluate it without conversational memory.

A record fails review when a future contributor must ask:

- What happened?
- Which repository, branch, issue, PR, or release is involved?
- What evidence supports this claim?
- Which statements are facts and which are interpretations?
- What changed as a result?

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

## Initial Record Set

The first worked example documents the Constitution v1.0 and Amendment A-0001 delivery:

- [FR-0001 — Constitutional release process failures](./FR-0001-constitutional-release-process.md)
- [RM-0001 — Why the release process required repeated recovery](./RM-0001-constitutional-release-process.md)
- [IER-0001 — Evolution of the constitutional baseline](./IER-0001-constitutional-baseline.md)
- [RL-0001 — Why failure-first institutional memory is required](./RL-0001-failure-first-memory.md)

## Maintenance

Records are append-only where historical claims are concerned. Corrections must preserve the prior statement, the correction, the evidence, and the date of change.

Success is not measured by the number of records produced. A record is valuable only when it helps a later contributor deliver, verify, maintain, or safely change the product.