# Issue 0009 — Objective-derived planning with task-level deliverable specs

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` B1
**Suggested labels:** `type:enhancement`, `type:epic`, `area:backend`, `track:quality`

## Summary
Replace generic plan generation with objective-derived decomposition that emits
explicit task deliverables, acceptance criteria, and dependencies.

## Problem
The current planner can default to overly generic plan shapes that do not match
the user's actual objective or the desired deliverable quality bar.

## Desired outcome
Planning should produce a fit-for-purpose multi-task structure that gives every
downstream task a concrete deliverable contract.

## Acceptance criteria
- [ ] Plan generation derives task structure from the actual objective instead
      of defaulting to a generic research-to-deliver flow.
- [ ] Every generated task includes an explicit deliverable description,
      acceptance criteria, and dependency information.
- [ ] Persisted plan data is rich enough for later execution, review, and UI
      display without reconstructing missing task contracts.
- [ ] Automated tests prove at least one objective that now decomposes into a
      materially different plan shape than the legacy fallback.

## Dependencies
- Planner prompt and persistence contract updates.
- UI support for rendering richer task metadata.

## Security and risk notes
- The richer plan contract must not allow unreviewed privilege expansion.
- Generated acceptance criteria should remain auditable as stored project state.
