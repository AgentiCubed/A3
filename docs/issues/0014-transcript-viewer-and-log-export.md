# Issue 0014 — Transcript viewer and one-click project log export

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` C2, C4  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:frontend`, `track:transparency`

## Summary
Provide a chronological transcript viewer and a one-click `project-log.md`
export so operators can inspect or share a full project run outside the live UI.

## Problem
Even if transcripts are stored, they are not useful enough until operators can
browse them easily and export a portable run log.

## Desired outcome
Projects should expose a searchable, chronological history view and an offline
markdown export generated from the same source of truth.

## Acceptance criteria
- [ ] A project-level viewer renders plan drafts, prompts, responses,
      evaluations, and remediation events in chronological order.
- [ ] Browser find works across the rendered history without hidden pagination
      breaking the flow.
- [ ] Operators can download a `project-log.md` export containing the same run
      history.
- [ ] Authorization and performance considerations are covered by tests or
      explicit implementation proof.

## Dependencies
- Transcript persistence from issue 0013.
- Frontend history page and export action.

## Security and risk notes
- Exported logs must inherit the same redaction guarantees as stored
  transcripts.
- Log access must stay scoped to authorized project viewers.
