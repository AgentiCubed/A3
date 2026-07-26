#!/usr/bin/env bash
set -euo pipefail

confirmation="${1:-}"
source_file="${2:-}"
env_file="${A3_ENV_FILE:-.env.prod}"
compose_file="${A3_COMPOSE_FILE:-docker-compose.prod.yml}"

if [[ "$confirmation" != "--confirm-restore" || -z "$source_file" ]]; then
  echo "usage: scripts/production_restore.sh --confirm-restore backups/a3.dump" >&2
  echo "DATABASE_RESTORE_URL must name the explicit restore target." >&2
  exit 2
fi
if [[ ! -f "$env_file" ]]; then
  echo "production env file not found: $env_file" >&2
  exit 2
fi
if [[ ! -s "$source_file" ]]; then
  echo "backup file is missing or empty: $source_file" >&2
  exit 2
fi

docker compose --env-file "$env_file" -f "$compose_file" \
  run -T --rm --no-deps db-tools \
  sh -ec '
    if [ -z "$DATABASE_RESTORE_URL" ]; then
      echo "DATABASE_RESTORE_URL is empty; refusing restore" >&2
      exit 2
    fi
    exec pg_restore \
      --exit-on-error \
      --clean \
      --if-exists \
      --no-owner \
      --dbname="$DATABASE_RESTORE_URL"
  ' <"$source_file"

echo "database restore completed against the explicit DATABASE_RESTORE_URL target"
