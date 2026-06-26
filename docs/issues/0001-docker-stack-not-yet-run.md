# Issue 0001 — Full Docker stack not yet exercised in this environment

**Status:** Open · **Opened:** 2026-06-25 · **Phase:** 1

## What is incomplete
The `docker compose up` path (db + redis + api + worker + frontend together) and
the live-Postgres Alembic apply have not been executed in the current build
environment. Backend and frontend were verified directly on the host instead
(native Python 3.12 venv + Node 26):

- `pytest` → 3 passed · `ruff`/`black` clean
- `vitest` → 5 passed · `tsc --noEmit` clean

## Why it is incomplete
Docker was not invoked in this session. The compose manifest, both Dockerfiles,
the Alembic baseline, and the `/readyz` db+redis checks are all written and
internally consistent, but an end-to-end container bring-up was not run, so the
following remain *verified-by-construction* rather than *verified-by-execution*:
- `/readyz` returning 200 with real db+redis
- Alembic `upgrade head` against a live Postgres 16
- Inter-service networking (api↔db↔redis, frontend↔api)

## Proposed resolution
Run `cp .env.example .env && make up`, then:
1. `curl localhost:8000/readyz` → expect `status: ok`, db+redis `ok`.
2. `make migrate` → baseline applies cleanly.
3. Load `localhost:3000` → dashboard shows API readiness checks.
Add a CI job (GitHub Actions service containers) that runs this on every push so
it stays verified. Target: close during Phase 2 CI setup.

## Dependencies
Docker / Docker Compose available in the execution environment or CI runner.

## Security implications
None introduced. `.env` is git-ignored; `.env.example` carries no real secrets.
Confirm the default dev `secret_key` is overridden before any non-local deploy
(already flagged in `docs/security-model.md`).
