# Issue 0008 — Rate-limit resilience and model fallback

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` A5  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:workers`, `track:live-runs`

## Summary
Handle provider 429s gracefully with bounded retries, exponential backoff, and
an optional configured fallback model.

## Problem
Free-tier and shared-provider usage can hit rate limits during normal work. A
single 429 currently creates avoidable operator churn and unnecessary project
failure.

## Desired outcome
Transient provider throttling should be retried automatically, and eligible
projects should be able to fail over to a fallback model without violating
project policy.

## Acceptance criteria
- [ ] Provider 429 responses trigger exponential backoff with a bounded retry
      policy.
- [ ] Retry timing and exhaustion state are visible in execution history.
- [ ] Projects can opt into a fallback model for supported task types.
- [ ] Automated coverage proves both eventual success after retry and terminal
      failure when the retry budget is exhausted.

## Dependencies
- Provider error classification.
- Project or task-level configuration for fallback behavior.

## Security and risk notes
- Fallback routing must remain within the project's approved model policy.
- Audit records must show which model actually executed each attempt.
