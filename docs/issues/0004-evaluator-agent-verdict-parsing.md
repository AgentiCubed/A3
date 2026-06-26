# Issue 0004 — Evaluator-agent verdict is advisory, not authoritative

**Status:** RESOLVED (2026-06-26) · **Opened:** 2026-06-25 · **Phase:** 6

## Resolution
The evaluator agent now produces an **influential** structured verdict that is
combined with the deterministic rubric (`evaluation_service.combine_verdicts` /
`agent_structured_verdict`): the combination takes the stricter of the two, so the
agent can downgrade a deterministic PASS (→ NEEDS_REVISION/FAIL) but can never
upgrade a hard deterministic FAIL. Verified by `test_verdict_combination`.

Residual (intentional): the structured verdict is still a deterministic stand-in,
not a live LLM judging through a provider tool/schema (kept so CI stays
provider-free, A15). Wiring a mock *structured-output* evaluator over the
`ToolSchema` port remains the upgrade path, but the agent verdict is no longer
ignored.

## What is incomplete
When an evaluation uses an evaluator **agent**, the agent produces a narrative
critique (stored in `Evaluation.summary`), but the **verdict/score** still come
from the deterministic rubric. The evaluator agent does not yet emit a structured
verdict that drives the gate.

## Why it is incomplete
A deterministic gate keeps the closed loop reproducible and the test-suite
provider-free (assumption A15). Trusting a free-text LLM verdict requires a
structured-output contract and careful parsing/validation, plus guardrails so a
miscalibrated judge can't rubber-stamp or over-reject.

## Proposed implementation
- Give the evaluator agent a structured-output tool/schema
  (`{verdict, score, per_criterion: [...]}`) via the provider adapter's tool
  interface.
- Combine deterministic + agent signals (e.g. deterministic is a hard floor; the
  agent can downgrade PASS→NEEDS_REVISION but not upgrade a hard FAIL).
- Add a mock evaluator that returns a deterministic structured verdict for tests.

## Dependencies
Provider adapter tool/structured-output support (the `ToolSchema` port exists;
wiring + a mock structured evaluator are the work).

## Security implications
Keep executor/evaluator separation (already enforced). Ensure the evaluator
cannot see or alter permissions; it only reads the output under review.
