# ADR-0006: Explicit lint targets over repo-wide exclusion

- **Status:** Accepted
- **Date:** 2026-07-16
- **Resolves:** Issue #5, item 1 (lint policy evaluation)

## Context

Two approaches to backend linting were under consideration (Issue #5):

1. **Explicit targets** — name the directories and files to lint:
   `ruff check app tests alembic/env.py`

2. **Repo-wide with exclusions** — lint everything and exclude generated code:
   `ruff check . --extend-exclude alembic/versions`

The question was raised during PR #1 review and deferred for independent evaluation.

## Decision

Keep the explicit-target approach as canonical in both the Makefile and CI.

## Rationale

The backend directory currently contains exactly three sets of Python source:

- `app/` — application code
- `tests/` — test suite
- `alembic/env.py` — hand-written migration environment

All three are already named in the explicit targets. The `alembic/versions/` directory contains only auto-generated migration files that should never be hand-edited and are not meaningful lint subjects.

Switching to repo-wide with exclusions would require maintaining an exclusion list to suppress false positives in generated code. The net coverage would be identical to what the explicit approach already provides.

The explicit approach has an additional advantage: it is self-documenting. Reading `ruff check app tests alembic/env.py` in the Makefile or CI log tells a reviewer immediately which code paths are verified, without requiring them to infer what the exclusion list omits.

If new hand-written Python directories are added (e.g., `scripts/`), they should be explicitly added to the lint targets in the Makefile and CI at the same time they are created.

## Consequences

- The Makefile `backend-lint` target and the CI lint step remain unchanged.
- New hand-written Python directories must be explicitly added to the lint command when introduced. This is a named, trackable action, not an implicit coverage extension.
- `alembic/versions/` files remain outside the lint scope, consistent with the convention that auto-generated code is not linted.
