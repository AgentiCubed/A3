# Issue 0013 — Persist full execution transcripts with redaction

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` C1  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:workers`, `track:transparency`

## Summary
Persist every prompt sent and response received for each execution attempt,
while redacting secrets before storage.

## Problem
Operators cannot reconstruct the full reasoning and remediation path of a run
because the most useful execution transcripts are not yet durably stored.

## Desired outcome
Execution records should preserve enough transcript detail for debugging,
review, and export without leaking secrets.

## Acceptance criteria
- [ ] Every execution attempt stores the full prompt/response transcript needed
      to reconstruct the run.
- [ ] Redaction is applied before any transcript content is persisted.
- [ ] Transcript records retain enough metadata to correlate them with task,
      attempt, model, provider, and timestamp information.
- [ ] Automated tests prove both transcript persistence and secret redaction.

## Dependencies
- Storage schema for transcript records.
- Redaction coverage for prompt and response payloads.

## Security and risk notes
- Secret scanning and redaction policy must treat transcripts as sensitive.
- Retention and export paths should assume transcripts may include private
  project context.
