# Issue 0006 — Provider errors and credential preflight

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` A2, A3  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:frontend`, `track:live-runs`

## Summary
Make live-provider failures legible before and after execution by translating
common provider failures into operator-facing messages and adding a cheap
preflight verification path.

## Problem
Live runs currently fail with low-signal provider errors. Operators can start a
project with a missing, malformed, or exhausted credential and only discover the
problem after work has already failed.

## Desired outcome
The system should surface actionable provider diagnostics before a project runs
and preserve human-readable failure reasons when a live execution still fails.

## Acceptance criteria
- [ ] Missing or malformed credentials, unknown model IDs, and provider rate
      limits map to distinct human-readable error messages in stored execution
      records and in the dashboard UI.
- [ ] A provider preflight check is available from the product surface before a
      live run starts and reports pass/fail without launching project work.
- [ ] The live-agent seed path exposes a non-destructive verification mode for
      operator setup.
- [ ] Automated tests cover the error mapping and the preflight failure modes.

## Dependencies
- Provider adapter error classification.
- Frontend status surface for preflight results.

## Security and risk notes
- Never echo raw secrets or provider payloads into UI or audit logs.
- Redaction rules must apply to all stored error and preflight details.
