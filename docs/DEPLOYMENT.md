# Deploying AgentiCubed — single-node production guide

Next-steps **Step 5** (gap G6). This is the smallest honest deployment story:
one host, Docker Compose, TLS on one domain, managed Postgres/Redis, and a
tested backup/restore procedure for the audit-bearing database. It is not a
high-availability story — see "Deliberately out of scope" at the end.

The moving parts:

```
browser ──https──▶ Caddy (TLS, port 443)
                     ├── /api/v1/*, /healthz ──▶ api (FastAPI + uvicorn)
                     └── everything else ──────▶ frontend (Next.js, compiled)
api ──┬─▶ Postgres (managed; the audit trail lives here)
      └─▶ Redis (event bus + Celery broker)
worker (Celery) ─▶ same Postgres/Redis; executes dispatched tasks
```

## 1. Prerequisites

- A Linux host with Docker Engine + the compose plugin, ports 80/443 open.
- A domain (e.g. `a3.example.com`) with a DNS **A record pointing at the
  host before first boot** — Caddy provisions the Let's Encrypt certificate
  on startup and needs the domain to resolve.
- Managed **PostgreSQL 16** and **Redis 7** instances (any cloud provider).
  A `--profile local-db` escape hatch runs both on the same box for trials,
  but the audit trail deserves a managed database with provider backups.

## 2. Configure

```bash
git clone <your fork> agenticubed && cd agenticubed
cp .env.prod.example .env.prod
chmod 600 .env.prod
openssl rand -hex 32   # → paste as SECRET_KEY
$EDITOR .env.prod      # domain/email, database, Redis, CORS, and provider keys
```

Notes that bite:

- `SECRET_KEY` signs sessions. The app **refuses to start** in production
  when it is blank, the template default, or shorter than 32 characters.
  Rotating it logs every user out (no data loss).
- `DATABASE_URL` (async, `+asyncpg`) and `DATABASE_URL_SYNC` (Alembic,
  `+psycopg`) must point at the **same** database. External Postgres and Redis
  URLs must require TLS; the checked-in example shows the expected forms.
- `CORS_ORIGINS` is just `https://<your domain>` — the deployment is
  same-origin by construction.
- Provider keys (`GITHUB_MODELS_TOKEN`, `ANTHROPIC_API_KEY`, …) are optional
  at boot: agents reference them by name (`api_key_ref`) and resolution
  happens at call time. Blank keys mean those providers refuse cleanly.

## 3. First boot

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
# self-contained trial instead (Postgres+Redis on this box):
#   add  --profile local-db  and point the URLs at db:5432 / redis:6379
```

The api container runs `alembic upgrade head` before binding — migrations
are applied automatically on every deploy. Verify:

```bash
curl -fsS https://<domain>/healthz     # {"status":"ok"}
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
scripts/prod_smoke.sh https://<domain>
```

Then open `https://<domain>`, register the first user (first registration
creates the organization), and run one governed project end to end with the
mock provider — the same loop CI proves — before pointing real work at it.

## 4. Backups — the audit trail is the product

Everything that matters (projects, tasks, executions, evaluations, approvals,
the audit ledger) lives in Postgres. Artifacts live in the `artifacts` volume.

**With a managed database (recommended):** enable the provider's automated
daily snapshots + point-in-time recovery, and *still* keep an encrypted,
off-provider logical dump. Set `DATABASE_BACKUP_URL` to a read-capable
PostgreSQL role in `.env.prod`, then run:

```bash
scripts/production_backup.sh "backups/a3-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

The helper creates a mode-`0600`, custom-format dump without source ownership
or ACL entries and refuses to overwrite an existing file.

**Restore drill — do this once now, not during an incident:**

```bash
createdb a3_restore_test
# Set DATABASE_RESTORE_URL in .env.prod to the separate restore-test database.
scripts/production_restore.sh --confirm-restore backups/a3-YYYYMMDD.dump
psql a3_restore_test -c "select count(*) from audit_events;"   # sanity
```

A backup that has never been restored is a hope, not a backup.

For an approved restore to the live production database, first stop every
writer, perform the explicit restore, then restart and run the smoke:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod stop proxy worker api
scripts/production_restore.sh --confirm-restore backups/a3-YYYYMMDD.dump
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
scripts/prod_smoke.sh https://<domain>
```

The restore helper uses `--clean --if-exists`; confirm the target URL and keep
the application quiesced for the entire operation.

**Artifacts volume:** `docker run --rm -v agenticubed_artifacts:/a -v "$PWD":/b
alpine tar czf /b/artifacts-$(date +%F).tgz -C /a .` alongside the DB dump.

## 5. Upgrades

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Migrations run automatically. Take a DB dump first (section 4) — Alembic
migrations here are forward-only; the rollback story is "restore the dump."

## 6. Operations

- **Health:** `/healthz` (liveness, public), `/readyz` (checks database and
  Redis; `scripts/prod_smoke.sh` checks both through the public TLS edge).
- **Metrics:** Prometheus at `/metrics` — deliberately **not** routed by
  Caddy; scrape it over the compose network or an SSH tunnel.
- **Logs:** `docker compose -f docker-compose.prod.yml --env-file .env.prod
  logs -f api worker` — structured JSON, no secrets (credentials are
  resolved by reference and never logged).
- **Halt switch:** an operator can pause all dispatch per project from the
  dashboard (Halt/Resume) — no server access needed.

## 7. Deliberately out of scope (for now)

Multi-node/HA topologies, Kubernetes, zero-downtime blue-green deploys,
object-store artifact backends, and autoscaling workers. The port
architecture (WorkflowEngine/EventBus/ArtifactStore) is where those grow
later; nothing in this guide paints over that door.
