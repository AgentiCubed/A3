# ADR-0006: Explicit lint targets over repo-wide exclusion

- **Status:** Superseded (by the v1.0.1 stabilization decision below)
- **Date:** 2026-07-16
- **Resolves:** Issue #5, item 1 (lint policy evaluation)

## Prior decision (as accepted)

Keep the explicit-target approach as canonical in both the Makefile and CI:

```
ruff check app tests alembic/env.py
black --check app tests alembic/env.py
```

### Rationale for the prior decision

The backend directory contained exactly three sets of hand-written Python source:

- `app/` — application code
- `tests/` — test suite
- `alembic/env.py` — hand-written migration environment

All three were named in the explicit targets. The `alembic/versions/` directory contains only
auto-generated migration files that should never be hand-edited and are not meaningful lint
subjects. Switching to repo-wide with exclusions would have required maintaining an exclusion
list to suppress false positives in generated code; net coverage would have been identical.

The explicit approach had an additional documentation advantage: reading
`ruff check app tests alembic/env.py` tells a reviewer immediately which code paths are
verified, without needing to infer what the exclusion list omits.

---

## Superseding decision (v1.0.1 stabilization)

**New canonical lint commands** (Makefile `backend-lint` and CI):

```
ruff check .
black --check .
```

Run from the `backend/` directory. `alembic/versions/` is excluded via
`extend-exclude` in `pyproject.toml`; `alembic/env.py` remains covered.

### Rationale for the superseding decision

1. **Automatic coverage of new hand-written Python files.** Any new file added under
   `backend/` (e.g. `scripts/`, `tasks/`) is automatically linted without requiring a
   separate Makefile/CI edit at the time of creation. This eliminates a category of
   lint-scope drift.

2. **Generated migrations remain excluded.** `alembic/versions/` is excluded from both
   Ruff and Black via `extend-exclude` in `pyproject.toml`, so auto-generated files are
   never reformatted or flagged.

3. **`alembic/env.py` remains covered.** The hand-written migration environment continues
   to be linted under repo-wide scope.

4. **Makefile and CI share the same command.** A single authoritative expression of lint
   scope reduces the chance of the two diverging.

5. **Reduces future drift.** Explicit targets require a named, trackable action whenever a
   new directory is added; repo-wide with exclusions shifts the burden to exclusions only
   for generated code — a smaller, more stable set.

### Consequences

- The Makefile `backend-lint` target and the CI lint step now use `ruff check .` and
  `black --check .`.
- `alembic/versions/` is excluded via `extend-exclude` in `pyproject.toml` (not via
  command-line flags), so the exclusion is shared by all tools and all invocations.
- New hand-written Python directories added to `backend/` are automatically covered.
- This ADR is retained under its original filename for citation stability; the prior
  decision is documented above.
