# Issue 0001 — Full Docker stack not yet exercised in this environment

**Status:** Mitigated (CI added in Phase 5) · **Opened:** 2026-06-25 · **Phase:** 1

## Update (Phase 5)
`.github/workflows/ci.yml` now runs the backend job against **real** Postgres 16 +
Redis 7 service containers: it applies `alembic upgrade head` to a live Postgres
and runs a `/readyz` smoke test asserting `database: ok` and `redis: ok`. This
closes the "migrations + readiness verified against real infra" gap on every
push/PR. A local `docker compose up` of all five services together still hasn't
been run in this build environment, so that specific path remains unverified
locally until CI runs or someone runs `make up`.

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
