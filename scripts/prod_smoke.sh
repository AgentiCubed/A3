#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-${A3_BASE_URL:-}}"
if [[ -z "$base_url" ]]; then
  echo "usage: scripts/prod_smoke.sh https://a3.example.com" >&2
  exit 2
fi
base_url="${base_url%/}"

case "$base_url" in
  https://*) ;;
  http://*)
    if [[ "${A3_ALLOW_HTTP:-0}" != "1" ]]; then
      echo "refusing a non-TLS URL; set A3_ALLOW_HTTP=1 only for a local test" >&2
      exit 2
    fi
    ;;
  *)
    echo "base URL must start with https://" >&2
    exit 2
    ;;
esac

curl_args=(
  --fail
  --silent
  --show-error
  --location
  --connect-timeout 5
  --max-time 20
  --retry 5
  --retry-connrefused
)

health_body="$(curl "${curl_args[@]}" "$base_url/healthz")"
printf '%s' "$health_body" | python3 -c '
import json
import sys

body = json.load(sys.stdin)
if body.get("status") != "ok":
    raise SystemExit(f"health check failed: {body}")
'

ready_body="$(curl "${curl_args[@]}" "$base_url/readyz")"
printf '%s' "$ready_body" | python3 -c '
import json
import sys

body = json.load(sys.stdin)
checks = body.get("checks", {})
if body.get("status") != "ok":
    raise SystemExit(f"readiness is degraded: {body}")
for dependency in ("database", "redis"):
    if checks.get(dependency) != "ok":
        raise SystemExit(f"{dependency} is not ready: {body}")
'

login_body="$(curl "${curl_args[@]}" "$base_url/login")"
if ! grep -q "Sign in" <<<"$login_body"; then
  echo "frontend smoke failed: login page did not contain the sign-in form" >&2
  exit 1
fi

echo "production smoke: PASS ($base_url)"
