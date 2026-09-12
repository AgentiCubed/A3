# Issue 0006 — Provider errors and credential preflight

**Status:** IMPLEMENTED · **Source:** `docs/MVP-ITERATION-TODO.md` A2, A3
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
- [x] Missing or malformed credentials, unknown model IDs, and provider rate
      limits map to distinct human-readable error messages in stored execution
      records and in the dashboard UI.
- [x] A provider preflight check is available from the product surface before a
      live run starts and reports pass/fail without launching project work.
- [x] The live-agent seed path exposes a non-destructive verification mode for
      operator setup.
- [x] Automated tests cover the error mapping and the preflight failure modes.

## Implementation notes
- `ProviderCallError.operator_message` / `human_message` in `app/orchestration/ports.py`
- `POST /api/v1/providers/preflight`, `GET /api/v1/providers`
- `python -m app.seed.live_agents --verify`
- Frontend: `humanizeProviderDiagnostic`, `ProviderReadiness` on the home page
- Proof: `tests/unit/test_provider_preflight.py`, `tests/integration/test_provider_preflight_api.py`,
  `frontend/tests/unit/error-detail.test.ts`, `ProviderReadiness.test.tsx`

## Dependencies
- Provider adapter error classification.
- Frontend status surface for preflight results.

## Security and risk notes
- Never echo raw secrets or provider payloads into UI or audit logs.
- Redaction rules must apply to all stored error and preflight details.
