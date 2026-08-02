# Issue 0010 — Executor context enrichment and deliverable templates

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` B2  
**Suggested labels:** `type:enhancement`, `area:backend`, `track:quality`

## Summary
Pass richer task context into execution prompts, including objective,
plan-derived task specs, predecessor outputs, and a task-appropriate
deliverable template.

## Problem
Execution prompts do not yet carry enough structured context to consistently
produce deliverables that align with the project objective and upstream work.

## Desired outcome
Every execution attempt should start with the context needed to produce the
right artifact on the first draft.

## Acceptance criteria
- [ ] Execution prompts include the project objective, the task's specific
      deliverable contract, predecessor outputs, and any task template required
      for the expected artifact.
- [ ] The prompt construction path is deterministic enough to inspect in tests
      and transcripts.
- [ ] Context enrichment works for both first-attempt execution and remediation
      retries.
- [ ] Automated coverage proves the enriched prompt assembly for at least one
      multi-task project.

## Dependencies
- Richer planning output from issue 0009.
- Transcript or debug visibility for prompt inspection.

## Security and risk notes
- Only project-scoped, authorized context may flow into the execution packet.
- Secret redaction rules must still apply to stored prompt payloads.
