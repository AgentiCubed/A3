# Issue 0007 — Dashboard failure visibility and retry flow

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` A4  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:frontend`, `track:live-runs`

## Summary
Expose blocked and escalated task failures directly in the dashboard and give
operators an explicit retry path after they apply a fix.

## Problem
Task failures are easy to miss because the actionable details live in backend
state rather than the primary UI. Operators also lack a first-class way to
retry work after correcting configuration or input problems.

## Desired outcome
The dashboard should make failure states self-explanatory and allow a deliberate
retry that preserves the audit trail.

## Acceptance criteria
- [ ] Blocked or escalated tasks show the current failure reason and remediation
      state in the dashboard without requiring direct database inspection.
- [ ] Operators can trigger a retry after fixing the underlying issue.
- [ ] The retry path is audited so the prior failure, the operator action, and
      the new attempt remain traceable.
- [ ] End-to-end coverage proves failure visibility and a successful retry from
      the browser.

## Dependencies
- Existing execution and remediation history.
- Frontend controls for retry eligibility and status updates.

## Security and risk notes
- Retry controls must honor existing authorization boundaries.
- UI error details must stay redacted and scoped to the project viewer.
