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

case "$BASE" in
https://*) ;;
http://*)
	[ "${A3_ALLOW_HTTP:-0}" = "1" ] || {
		echo "refusing a non-TLS URL; set A3_ALLOW_HTTP=1 only for a local test" >&2
		exit 2
	}
	;;
*)
	echo "base URL must start with https://" >&2
	exit 2
	;;
esac

echo "1/3 API liveness through the proxy…"
body="$(curl -fsS --connect-timeout 5 --max-time 20 --retry 5 --retry-connrefused "$BASE/healthz")" ||
	fail "/healthz unreachable"
printf "%s" "$body" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' ||
	fail "/healthz answered without status ok: $body"
echo "    ok"

echo "2/3 API refuses unauthenticated access…"
code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 \
	"$BASE/api/v1/projects")" || fail "/api/v1/projects unreachable"
[ "$code" = "401" ] || [ "$code" = "403" ] || fail "expected 401/403 from /api/v1/projects, got $code"
echo "    ok ($code)"

echo "3/3 frontend serves…"
code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 -L \
	"$BASE/")" || fail "/ unreachable"
[ "$code" = "200" ] || fail "expected 200 from /, got $code"
echo "    ok"

echo "SMOKE PASS: $BASE"
