# Issue 0011 — Draft/review loop, live rubrics, and per-task model routing

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` B3, B4, B6  
**Suggested labels:** `type:enhancement`, `type:epic`, `area:backend`, `area:workers`, `track:quality`

## Summary
Introduce a configurable draft → self-review → revise loop, derive evaluator
rubrics from the objective and task contract, and route different task steps to
appropriate model tiers.

## Problem
The current quality loop is too shallow: draft generation, evaluation, and model
selection do not yet adapt enough to task type or deliverable expectations.

## Desired outcome
The system should iteratively improve task outputs before independent evaluation
and use the right model for the right step.

## Acceptance criteria
- [ ] Projects can configure the maximum self-revision iterations per task.
- [ ] Task evaluation criteria derive from the objective and persisted task
      acceptance criteria rather than relying on minimal generic checks.
- [ ] Planning, drafting, review, and mechanical follow-up steps can route to
      different configured model tiers.
- [ ] Execution history records how many internal revision passes ran and which
      model handled each stage.
- [ ] Automated coverage proves iteration bounds, rubric derivation, and model
      selection behavior.

## Dependencies
- Richer task contracts from issue 0009.
- Execution-context work from issue 0010.

## Security and risk notes
- Model routing must not bypass configured provider or approval boundaries.
- Additional internal passes must stay within explicit budget controls.
