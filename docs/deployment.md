# Single-node production deployment

This is the smallest supported production shape for AgentiCubed: one Linux
host runs the API, Celery worker, Next.js frontend, and Caddy edge proxy.
PostgreSQL and Redis are managed services outside the host.

Kubernetes, Temporal, multi-host failover, and automatic horizontal scaling are
not part of this deployment contract.

## Architecture and boundaries

```text
Internet
   |
   | 80/443
   v
Caddy (automatic TLS)
   |--------------------> Next.js frontend
   | /api/v1, /healthz,
   | /readyz
   v
FastAPI API -----> managed PostgreSQL 16 (audit-bearing system of record)
     |
     +-----------> managed Redis 7 (events, broker, result backend)
                         ^
                         |
                    Celery worker

API + worker -----> host-local named artifact volume
```

Only Caddy publishes host ports. The API, worker, and frontend stay on the
private Compose network. Caddy obtains and renews TLS certificates
automatically after DNS points at the host and ports 80/443 are reachable.

## Prerequisites

- A current Linux host with Docker Engine and Docker Compose.
- DNS `A`/`AAAA` records for the production hostname.
- Inbound firewall access only for SSH administration, TCP 80, TCP 443, and
  UDP 443. Do not publish PostgreSQL, Redis, API port 8000, or frontend port
  3000.
- Managed PostgreSQL 16 with TLS, automated backups, and point-in-time
  recovery.
- Managed Redis 7 with TLS and an ACL-scoped account.

## 1. Configure secrets

```bash
cp .env.production.example .env.production
chmod 600 .env.production
openssl rand -hex 32
```

Put the generated value in `SECRET_KEY`, replace every managed-service URL,
and set `A3_DOMAIN`, `ACME_EMAIL`, and `CORS_ORIGINS`. Credentials containing
special characters must be URL-encoded.

`.env.production` is read at container creation time. It is ignored by Git and
must never be baked into an image. On a managed container platform, inject the
same variables through its secret store instead of copying this file.

Production startup refuses template/short JWT secrets and wildcard CORS.

## 2. Validate and deploy

Use the Git SHA as the local image tag so a deployment has an exact source
identity:

```bash
export A3_IMAGE_TAG="$(git rev-parse --short=12 HEAD)"
docker compose --env-file .env.production -f compose.production.yml config -q
docker compose --env-file .env.production -f compose.production.yml build api frontend
docker compose --env-file .env.production -f compose.production.yml up -d
docker compose --env-file .env.production -f compose.production.yml ps
```

The API applies Alembic migrations before it starts accepting traffic. The
worker and frontend wait for API readiness, and Caddy waits for both.

## 3. Smoke and operate

Run the public smoke from outside the host so DNS, certificate validation,
proxy routing, frontend rendering, and managed-service readiness are all in
the proof:

```bash
scripts/production_smoke.sh "https://${A3_DOMAIN}"
```

The smoke fails unless:

- TLS validates normally;
- `/healthz` reports `ok`;
- `/readyz` reports both PostgreSQL and Redis as `ok`; and
- the frontend serves the sign-in form.

Operational commands:

```bash
docker compose --env-file .env.production -f compose.production.yml ps
docker compose --env-file .env.production -f compose.production.yml logs -f --tail=100
docker compose --env-file .env.production -f compose.production.yml restart worker
```

## 4. Back up and restore the audit-bearing database

Managed point-in-time recovery is the primary protection. Also create an
encrypted, off-host logical backup before every migration and at least daily.
`DATABASE_BACKUP_URL` should use a role allowed to read all application tables.

```bash
scripts/production_backup.sh "backups/a3-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

The helper creates a PostgreSQL custom-format dump with mode `0600` and refuses
to overwrite an existing file. Move it immediately to encrypted off-host
storage with a documented retention policy.

Restore is deliberately harder. First rehearse against a separate database,
set `DATABASE_RESTORE_URL` to that explicit target, and verify the smoke there.
Only use a production target during an approved recovery window:

```bash
scripts/production_restore.sh --confirm-restore backups/a3-YYYYMMDD.dump
```

The restore helper refuses to run without both the confirmation flag and a
non-empty `DATABASE_RESTORE_URL`. It uses `--clean --if-exists`; restoring to a
populated target replaces database objects represented by the dump.

The `a3_artifacts` volume is not stored in PostgreSQL. Back it up separately
whenever real artifact retention matters.

## 5. Upgrade and rollback

1. Create and verify a logical database backup.
2. Fetch the intended release, set `A3_IMAGE_TAG` to its exact SHA, rebuild,
   run `up -d`, and run the public smoke.

For an application-only rollback, check out the prior SHA, rebuild with that
tag, and run `up -d`. Database migrations are forward-only: if a release
requires database rollback, stop the stack and restore the pre-deployment dump
under the explicit recovery procedure above.

This runbook proves a repeatable deployment contract. A real production claim
still requires an operator-recorded deployment, successful public smoke, and a
restore rehearsal against the chosen managed providers.
