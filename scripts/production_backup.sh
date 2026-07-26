#!/usr/bin/env bash
set -euo pipefail

target="${1:-}"
env_file="${A3_ENV_FILE:-.env.prod}"
compose_file="${A3_COMPOSE_FILE:-docker-compose.prod.yml}"

if [[ -z "$target" ]]; then
  echo "usage: scripts/production_backup.sh backups/a3-YYYYMMDD.dump" >&2
  exit 2
fi
if [[ ! -f "$env_file" ]]; then
  echo "production env file not found: $env_file" >&2
  exit 2
fi
if [[ -e "$target" ]]; then
  echo "refusing to overwrite existing backup: $target" >&2
  exit 2
fi

mkdir -p "$(dirname "$target")"
umask 077
temporary="$(mktemp "${target}.tmp.XXXXXX")"
trap 'rm -f "$temporary"' EXIT

docker compose --env-file "$env_file" -f "$compose_file" \
  run -T --rm --no-deps db-tools \
  sh -ec 'exec pg_dump --format=custom --no-owner --dbname="$DATABASE_BACKUP_URL"' \
  >"$temporary"

if [[ ! -s "$temporary" ]]; then
  echo "backup produced an empty file" >&2
  exit 1
fi

mv "$temporary" "$target"
trap - EXIT
echo "database backup created: $target"
