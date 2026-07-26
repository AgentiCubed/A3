#!/usr/bin/env sh
# Post-deploy smoke for the production compose profile (docs/DEPLOYMENT.md §3).
#
#   ./scripts/prod_smoke.sh https://a3.example.com
#
# Proves the three public routing legs work: the API answers through the
# proxy, unauthenticated API access is refused (auth is on), and the
# frontend serves. Exits non-zero on the first failure.

set -eu

BASE="${1:?usage: prod_smoke.sh https://your-domain}"
BASE="${BASE%/}"

fail() {
	echo "SMOKE FAIL: $1" >&2
	exit 1
}

echo "1/3 API liveness through the proxy…"
body="$(curl -fsS --max-time 10 "$BASE/healthz")" || fail "/healthz unreachable"
case "$body" in
*ok*) echo "    ok" ;;
*) fail "/healthz answered without status ok: $body" ;;
esac

echo "2/3 API refuses unauthenticated access…"
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$BASE/api/v1/projects")"
[ "$code" = "401" ] || [ "$code" = "403" ] || fail "expected 401/403 from /api/v1/projects, got $code"
echo "    ok ($code)"

echo "3/3 frontend serves…"
code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 -L "$BASE/")"
[ "$code" = "200" ] || fail "expected 200 from /, got $code"
echo "    ok"

echo "SMOKE PASS: $BASE"
