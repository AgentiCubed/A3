# Institutional Knowledge Record Templates

## Shared Lifecycle Fields

Use the following fields whenever they help make a record reusable and auditable:

```markdown
## Validation State
Captured | Reviewed | Validated | Superseded | Retired

## Memory Layer
Working | Project | Institutional | Evolution

## Capture Trigger
What event, observation, or decision required this record now?

## Stable References
Issue, PR, commit SHA, release, ADR, decision record, log, or file path.

## Supersession
Replaces: <record id or none>
Superseded by: <record id or none>
```

Decision records are not duplicated here:

- governance decisions use `docs/governance/decisions/`;
- architectural decisions use `docs/decisions/`.

Knowledge records should link to those decisions instead of creating a second decision namespace.

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

## Linked Records
Related FR, RM, IER, TET, ADR, issue, PR, or release.
```

## Traceable Epistemic Transition — `TET-NNNN`

```markdown
# TET-NNNN — Title

## Prior Model
The belief, prediction, or design assumption before the change.

## Disturbing Evidence
The observation, test result, incident, or argument that challenged the prior model.

## Revised Model
What is believed now.

## Tested Consequence
What changed in behavior, implementation, or verification as a result.

## Confidence Shift
How confidence changed and why.

## Scope of Reuse
Where this transition should and should not be reused.

## Linked Records
Related FR, RM, IER, RL, experiment, issue, PR, ADR, or release.
```

## Pattern — `PAT-NNNN`

```markdown
# PAT-NNNN — Name

## Status
Candidate | Validated | Superseded | Retired

## Problem Shape
What recurring situation this pattern addresses.

## Pattern Statement
The reusable solution shape.

## Preconditions
Conditions that should be true before applying the pattern.

## Evidence for Reuse
Cases, records, or releases showing that the pattern worked.

## Failure Modes
How the pattern can fail or be misapplied.

## When Not to Use
Conditions under which another approach is preferable.

## Linked Records
Related FR, RM, RL, TET, ADR, issue, PR, or release.
```

## Anti-pattern — `APAT-NNNN`

```markdown
# APAT-NNNN — Name

## Status
Observed | Validated | Superseded | Retired

## Harmful Shape
The recurring approach that creates avoidable harm.

## Observable Damage
What failure, delay, confusion, or false confidence it causes.

## Evidence
Incidents, records, or releases showing the harm.

## Safer Alternative
Which pattern, heuristic, or control should replace it.

## Early Warning Signs
Signals that the anti-pattern is emerging again.

## Linked Records
Related FR, RM, RL, TET, issue, PR, ADR, or release.
```

## Risk — `RSK-NNNN`

```markdown
# RSK-NNNN — Title

## Status
Open | Monitoring | Mitigated | Realized | Superseded | Retired

## Risk Statement
The uncertain condition and the harm it could cause.

## Scope
Which repository area, release, workflow, or architectural layer is affected.

## Triggers / Leading Indicators
Signals that the risk is increasing or beginning to realize.

## Impact
What would be harmed and how severely.

## Mitigations
Current controls or planned actions.

## Verification / Monitoring
How the project will know the mitigation worked or the risk changed.

## Review Trigger
Date, event, or threshold that requires re-evaluation.

## Linked Records
Related assumption, experiment, FR, ADR, issue, PR, or release.
```

## Assumption — `ASM-NNNN`

```markdown
# ASM-NNNN — Title

## Status
Open | Partially Validated | Validated | Invalidated | Superseded

## Statement
The premise currently being relied on.

## Why It Is Needed
Why work cannot proceed cleanly without this assumption.

## Evidence Present
What currently supports the assumption, if anything.

## Validation Method
How the assumption will be tested.

## Invalidating Evidence
What result would prove the assumption false or unsafe.

## Dependent Decisions
Which designs, experiments, risks, or releases rely on this assumption.

## Linked Records
Related RL, experiment, ADR, issue, PR, or release.
```

## Experiment — `EXP-NNNN`

```markdown
# EXP-NNNN — Title

## Status
Planned | Running | Completed | Inconclusive | Superseded

## Question
What uncertainty the experiment is intended to resolve.

## Hypothesis
The predicted outcome.

## Boundary
What will be changed, measured, or observed, and what remains out of scope.

## Method
The test, prototype, benchmark, or comparison being used.

## Success Criteria
The observable result that would support the hypothesis.

## Failure / Rejection Criteria
The observable result that would weaken or reject the hypothesis.

## Results
Observed outputs, measurements, and anomalies.

## Decision Impact
Which assumptions, risks, patterns, or decisions change because of the result.

## Linked Records
Related assumption, risk, RL, TET, issue, PR, ADR, or release.
```

## Unexpected Success Record — `USR-NNNN`

```markdown
# USR-NNNN — Title

## Status
Captured | Under Review | Validated | Superseded

## Unexpected Outcome
What succeeded beyond expectation or without prior prediction.

## Conditions Present
The context, constraints, and setup at the time of success.

## Evidence
Verification output, metrics, commits, logs, or observed behavior.

## Why It May Have Worked
Candidate explanations, clearly separated from verified fact.

## Reuse Candidate
What should be repeated, tested further, or promoted into a pattern.

## Remaining Uncertainty
What is still not understood.

## Linked Records
Related pattern, experiment, RL, issue, PR, ADR, or release.
```

## Record Quality Gate

A record passes only when:

- facts, inference, hypotheses, and decisions are visibly separated;
- all external references are stable and inspectable;
- a reviewer needs no conversational memory;
- responsibility is preserved without blame theater;
- the record produces a reusable decision, heuristic, or open question;
- omissions and uncertainty are stated rather than hidden.
