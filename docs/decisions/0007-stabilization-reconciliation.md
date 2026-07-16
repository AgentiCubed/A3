# ADR-0007: Remaining stabilization reconciliations from superseded PR #1

- **Status:** Accepted
- **Date:** 2026-07-16
- **Resolves:** Issue #5, items 2-4
- **Related:** ADR-0006 (lint policy)

## Context

Issue #5 split the stabilization ideas from superseded PR #1 into independent
decisions. ADR-0006 records the lint-policy outcome. The remaining questions
were about the `/readyz` smoke test, demo documentation, and CI teardown.

## Decision

### 1. Readiness endpoint assertions

The canonical CI smoke test shall parse the `/readyz` response as JSON and
assert semantic fields, rather than matching the raw response string.

The accepted assertions are:

- `checks.database == "ok"`
- `checks.redis == "ok"`

Whitespace-tolerant string matching was considered, but JSON parsing is the
more robust long-term choice because it validates the response contract instead
of the serializer's formatting.

### 2. Canonical demo documentation

The canonical host-side demo invocation remains the repo-root command:

```bash
make demo
```

The README should keep that command visible and link to `docs/demo.md` for the
detailed walkthrough and programmatic/test-oriented usage notes.

### 3. Server teardown in CI

The readiness smoke test teardown shall tolerate the server process already
having exited:

```bash
kill $SERVER_PID
wait $SERVER_PID || true
```

This keeps cleanup deterministic while avoiding false CI failures when the
process stops before `wait` observes it.

## Consequences

- `.github/workflows/ci.yml` remains aligned with semantic `/readyz` assertions
  and tolerant teardown.
- `README.md` remains the authoritative top-level entry point for the host-side
  demo command, while `docs/demo.md` carries the detail.
- PR #1 can be treated as superseded without reopening its combined change set.
