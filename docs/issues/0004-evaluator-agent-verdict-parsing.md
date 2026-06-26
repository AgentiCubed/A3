# Issue 0004 — Evaluator-agent verdict is advisory, not authoritative

**Status:** Open · **Opened:** 2026-06-25 · **Phase:** 6

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
