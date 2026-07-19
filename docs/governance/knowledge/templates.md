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
Related RM, IER, RL, TET, issue, PR, or release.
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
Related FR, RM, RL, TET, ADR, issue, PR, or release.
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

## Traceable Epistemic Transition capsule — `TET-NNNN`

```markdown
# TET-NNNN — Title

## Prior Model
The belief or operating model before the transition.

## Disturbing Evidence
The observation, failure, experiment, or argument that contradicted the prior model.

## Revised Model
The updated understanding after considering the evidence.

## Tested Consequence
What was done to test the revised model and what happened.

## Confidence Change
How confidence changed and why.

## Reopening Conditions
What new evidence would require another update.

## Linked Records
Related FR, RM, IER, RL, Pattern, ADR, issue, PR, or release.
```

## Pattern — `PAT-NNNN`

```markdown
# PAT-NNNN — Title

## Status
Active | Validated | Superseded | Retired

## Problem
What recurring situation this pattern addresses.

## Pattern
The reusable behavior or structure.

## Why It Works
The mechanism believed to produce the benefit.

## Evidence
Independent uses, metrics, or linked records.

## Applicability
When to use it.

## Boundaries
When not to use it.

## Failure Modes
How misuse can go wrong.

## Linked Records
Related FR, RM, IER, RL, TET, Anti-pattern, ADR, issue, or PR.
```

## Anti-pattern — `AP-NNNN`

```markdown
# AP-NNNN — Title

## Status
Active | Validated | Superseded | Retired

## Signal
What recurring harmful behavior or structure should be recognized.

## Why It Fails
The mechanism that creates the harm.

## Evidence
Observed recurrences, incidents, or linked records.

## Early Warning Signs
How to detect it before damage grows.

## Safer Alternative
Pattern or behavior that should replace it.

## Known Exceptions
Cases where the anti-pattern label does not apply.

## Linked Records
Related FR, RM, IER, RL, TET, Pattern, ADR, issue, or PR.
```

## Risk — `RSK-NNNN`

```markdown
# RSK-NNNN — Title

## Status
Open | Watching | Mitigated | Realized | Retired

## Risk Statement
The material downside being tracked.

## Context
Where and why the risk matters.

## Trigger
What condition would activate or worsen the risk.

## Evidence
Signals, prior incidents, measurements, or linked records.

## Likelihood / Confidence
Qualitative or quantitative estimate with basis.

## Impact
What is at stake.

## Mitigation
What reduces likelihood or impact.

## Owner
Who is responsible for watching it.

## Review Trigger
When the risk must be reassessed.
```

## Assumption — `ASM-NNNN`

```markdown
# ASM-NNNN — Title

## Status
Open | Monitoring | Validated | Rejected | Superseded

## Assumption
The unverified premise currently being relied on.

## Why It Is Being Assumed
Why work is proceeding before proof exists.

## Supporting Indications
Weak evidence or rationale that makes the assumption plausible.

## Invalidating Signals
Evidence that would show the assumption is wrong.

## Consequence If Wrong
What work, design, or governance would be affected.

## Owner
Who is responsible for re-checking it.

## Review Trigger
When it must be revisited.
```

## Experiment — `EXP-NNNN`

```markdown
# EXP-NNNN — Title

## Status
Planned | Running | Observed | Closed | Superseded

## Question
What uncertainty the experiment is intended to reduce.

## Hypothesis
What is expected and why.

## Method
How the test will be run.

## Guardrails
Limits that keep the experiment safe and interpretable.

## Evidence
Data, artifacts, or observations produced.

## Result
What happened.

## Decision Impact
How the result changes design, policy, or confidence.

## Follow-up
What should happen next.
```

## Unexpected Success Record — `USR-NNNN`

```markdown
# USR-NNNN — Title

## Status
Observed | Reused | Validated | Superseded

## Context
What work was being attempted.

## Expected Difficulty or Outcome
What was expected instead.

## Observed Success
What worked materially better than expected.

## Evidence
Commands, metrics, diffs, logs, feedback, or linked records.

## Candidate Explanation
Why the success may have happened.

## Reuse Conditions
When it may be safe to try again.

## Overgeneralization Risk
How this success could mislead future work if copied too broadly.

## Linked Records
Related Pattern, Experiment, RL, issue, PR, or release.
```

## Record Quality Gate

A record passes only when:

- facts, inference, hypotheses, and decisions are visibly separated;
- all external references are stable and inspectable;
- a reviewer needs no conversational memory;
- responsibility is preserved without blame theater;
- the record states authority or ownership where relevant;
- the record produces a reusable decision, heuristic, or open question;
- reopening conditions or review triggers are explicit;
- omissions and uncertainty are stated rather than hidden.
