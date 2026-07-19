# Institutional Knowledge Record Templates

## Failure Record — `FR-NNNN`

```markdown
# FR-NNNN — Title

## Status
Open | Contained | Verified | Superseded

## Context
Repository, branch, issue, PR, release, date, and actors or systems involved.

## Observed Behavior
Only directly observed facts.

## Expected Behavior
The documented or authorized expectation.

## Evidence
Commands, exit codes, URLs, screenshots, logs, commits, diffs, or files.

## Impact
Delivery, safety, verification, maintainability, authority clarity, auditability, or continuity.

## Immediate Correction
What was done to contain or correct the failure.

## Verification
Evidence that the correction worked.

## Unresolved Facts
What remains unknown.

## Linked Records
Related RM, IER, RL, issue, PR, or release.
```

## Rumination — `RM-NNNN`

```markdown
# RM-NNNN — Title

## Linked Failure
FR-NNNN

## Question
What deeper question does the failure expose?

## Verified Facts
Facts inherited from the linked Failure Record.

## Hypotheses
Competing explanations, each labeled with confidence.

## Counter-Evidence
Evidence that weakens each hypothesis.

## Rejected Explanations
What was considered and why it was rejected.

## Human and System Factors
Interface, incentives, cognitive load, process, tooling, and organizational conditions.

## Mental Model Update
What belief changed and why.

## Generalized Principle
A reusable principle stated narrowly enough to test.

## Future Heuristics
Concrete behavior for the next comparable situation.

## Remaining Uncertainty
What evidence would change the conclusion.
```

## Idea Evolution Record — `IER-NNNN`

```markdown
# IER-NNNN — Idea

## Current Formulation
The present understanding.

## Stage 1 — Initial Idea
Claim, assumptions, and context.

## Stage 2 — First Revision
Contradiction, evidence, and change.

## Stage 3 — Later Revision
Further evidence, discarded branches, and change.

## Current Decision
What is accepted now and by whom.

## Reopening Conditions
Evidence or context that would justify reconsideration.

## Linked Records
Related FR, RM, RL, ADR, issue, PR, or release.
```

## Reasoning Ledger — `RL-NNNN`

```markdown
# RL-NNNN — Decision or Claim

## Claim
The proposition being evaluated.

## Decision Authority
Who may decide or ratify.

## Assumptions
Explicit premises.

## Evidence
Evidence supporting the claim.

## Counter-Evidence
Evidence weakening the claim.

## Alternatives Considered
Competing options.

## Why Rejected
Reasoning for each rejection.

## Confidence Before
Qualitative or numeric confidence before evaluation, with basis.

## Trigger That Changed Confidence
The specific observation or argument that caused the update.

## Confidence After
Updated confidence, with basis.

## Remaining Uncertainty
Unknowns and evidence required.

## Decision
Accepted | Accepted with Modification | Deferred | Rejected

## Review Date or Trigger
When or under what condition the ledger must be revisited.
```

## Record Quality Gate

A record passes only when:

- facts, inference, hypotheses, and decisions are visibly separated;
- all external references are stable and inspectable;
- a reviewer needs no conversational memory;
- responsibility is preserved without blame theater;
- the record produces a reusable decision, heuristic, or open question;
- omissions and uncertainty are stated rather than hidden.