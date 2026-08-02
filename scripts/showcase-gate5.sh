#!/usr/bin/env bash
#
# Gate 5 — build the clean staging repository for the public showcase.
#
#   ./scripts/showcase-gate5.sh
#
# What it does: copies showcase/ into a brand-new throwaway folder, runs every
# safety check against those exact bytes, then makes ONE commit with a
# public-safe identity.
#
# What it does NOT do, ever: talk to GitHub, add a remote, push, create a
# repository, or make anything public. Those are Gate 6 and Gate 8, and they
# are yours.
#
# It stops at the FIRST failure. A stop is the script working. Read the message,
# fix the cause in showcase/, delete the staging folder it names, and run it
# again from the top. Never fix something inside the staging folder — the whole
# point is that the staging folder is a faithful copy of showcase/.
#
# Full context: docs/showcase/PUBLICATION-CONTROL-GATES.md

set -euo pipefail

# ── Identity used for the publication commit ────────────────────────────────
# GitHub's no-reply address for JamesTRichmond (account ID 170839886). This
# keeps a real email address out of a permanently public git history.
# Override if needed:  GIT_AUTHOR_NAME_OVERRIDE=... GIT_EMAIL_OVERRIDE=... ./script
COMMIT_NAME="${GIT_AUTHOR_NAME_OVERRIDE:-James T. Richmond}"
COMMIT_EMAIL="${GIT_EMAIL_OVERRIDE:-170839886+JamesTRichmond@users.noreply.github.com}"
COMMIT_MESSAGE="AgentiCubed public showcase"

# ── Pretty output ───────────────────────────────────────────────────────────
if [ -t 1 ]; then
  RED=$'\033[31m'; GRN=$'\033[32m'; YEL=$'\033[33m'; BLD=$'\033[1m'; RST=$'\033[0m'
else
  RED=''; GRN=''; YEL=''; BLD=''; RST=''
fi

STEP=0
step()  { STEP=$((STEP+1)); printf '\n%s── %s. %s%s\n' "$BLD" "$STEP" "$1" "$RST"; }
pass()  { printf '   %sPASS%s  %s\n' "$GRN" "$RST" "$1"; }
warn()  { printf '   %sWARN%s  %s\n' "$YEL" "$RST" "$1"; }
info()  { printf '         %s\n' "$1"; }

STAGE=""
fail() {
  printf '\n%s╔══════════════════════════════════════════════════════════╗%s\n' "$RED" "$RST"
  printf '%s║  GATE 5 STOPPED — nothing was published                   ║%s\n' "$RED" "$RST"
  printf '%s╚══════════════════════════════════════════════════════════╝%s\n' "$RED" "$RST"
  printf '\n%sReason:%s %s\n' "$BLD" "$RST" "$1"
  if [ -n "$STAGE" ] && [ -d "$STAGE" ]; then
    printf '\nFix the cause in showcase/, then remove the staging folder and rerun:\n'
    printf '  rm -rf %q\n' "$STAGE"
  fi
  printf '\nDo not edit files inside the staging folder. Fix showcase/ and start over.\n\n'
  exit 1
}

# Runs a command; fails the gate if it printed anything.
expect_empty() {
  local label="$1"; shift
  local out
  out="$("$@" 2>/dev/null || true)"
  if [ -n "$out" ]; then
    printf '\n%s\n' "$out"
    fail "$label — the output above must have been empty."
  fi
  pass "$label"
}

# Runs a grep; fails the gate if it matched anything.
expect_no_match() {
  local label="$1"; shift
  local out
  out="$(grep "$@" 2>/dev/null || true)"
  if [ -n "$out" ]; then
    printf '\n%s\n' "$out"
    fail "$label — the matches above must not be present."
  fi
  pass "$label"
}

# ── 1. Locate the source tree ───────────────────────────────────────────────
step "Locate the showcase source"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC="$REPO_ROOT/showcase"
[ -d "$SRC" ] || fail "No showcase/ folder at $SRC. Run this from inside the private repo."
[ -f "$REPO_ROOT/docs/showcase/PUBLICATION-CONTROL-GATES.md" ] \
  || warn "Control document not found where expected — check you are in the right repo."
pass "source: $SRC"

# ── 2. Tool preflight ───────────────────────────────────────────────────────
step "Check the tools this gate needs"
command -v git >/dev/null || fail "git is not installed."
pass "git $(git --version | awk '{print $3}')"

if command -v python3 >/dev/null 2>&1 && python3 -c '1' >/dev/null 2>&1; then
  HAVE_PY=1; pass "python3 (used for JSON and link checks)"
else
  HAVE_PY=0
  warn "python3 not available — JSON and link checks will be skipped."
  info "Install with: xcode-select --install"
fi

if command -v gitleaks >/dev/null 2>&1; then
  HAVE_GITLEAKS=1; pass "gitleaks $(gitleaks version 2>/dev/null || echo '?')"
else
  HAVE_GITLEAKS=0
  warn "gitleaks NOT installed — the dedicated secret scan will be SKIPPED."
  info "Strongly recommended. Install with:  brew install gitleaks"
  info "Then rerun this script. The pattern scans below are a backstop, not a"
  info "replacement — gitleaks catches shapes a hand-written grep will miss."
fi

# ── 3. Brand-new staging folder ─────────────────────────────────────────────
step "Create a one-use staging folder"
STAGE="$(mktemp -d "${TMPDIR:-/tmp}/agenticubed-showcase.XXXXXX")"
[ -n "$STAGE" ] && [ -d "$STAGE" ] || fail "Could not create a staging folder."
[ -z "$(find "$STAGE" -mindepth 1 -print -quit)" ] || fail "Staging folder is not empty."
pass "created and confirmed empty: $STAGE"

# ── 4. Copy ─────────────────────────────────────────────────────────────────
step "Copy showcase/ contents into staging"
cp -R "$SRC"/. "$STAGE"/
cd "$STAGE"
FILE_COUNT="$(find . -type f | wc -l | tr -d ' ')"
pass "$FILE_COUNT files copied"

# ── 5. Read the inventory ───────────────────────────────────────────────────
step "The complete list of what you are about to publish — READ IT"
find . -type f | LC_ALL=C sort | sed 's/^\./   /'
printf '\n'
read -r -p "   Does every line above belong in a public repo? [yes/no] " ANSWER
case "$ANSWER" in
  yes|YES|y|Y) pass "inventory confirmed by operator" ;;
  *) fail "Operator did not confirm the inventory." ;;
esac

# ── 6. Boundary checks ──────────────────────────────────────────────────────
step "Boundary — nothing may leak in through the file system"
expect_empty "no symlinks (a symlink's target is a hidden path leak)" \
  find . -type l
expect_empty "no nested git metadata" \
  find . \( -name .git -o -name .gitmodules \) -print
expect_empty "no OS droppings (.DS_Store etc.)" \
  find . \( -name '.DS_Store' -o -name 'Thumbs.db' -o -name 'desktop.ini' -o -name '._*' \) -print
expect_empty "no private control documents" \
  find . -iname '*PUBLICATION*' -print
expect_empty "no GitHub Actions workflows" \
  find . -path './.github/workflows*' -print

# ── 7. Content scans ────────────────────────────────────────────────────────
step "Content — secret shapes, credentials, personal and private references"
expect_no_match "no secret-shaped values (AWS, Slack, GitHub, OpenAI, Google, GitLab, SendGrid, JWT)" \
  -RnE 'AKIA[0-9A-Z]|ASIA[0-9A-Z]|eyJ[A-Za-z0-9_-]{10}|xox[abprs]-|sk-ant-|sk-[A-Za-z0-9_-]{8}|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|glpat-|AIza[0-9A-Za-z_-]|SG\.[A-Za-z0-9_-]{10}' .
expect_no_match "no credential-bearing connection strings or webhook URLs" \
  -RniE '(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqps?|smtps?|ftp)://[^ \"]*@|hooks\.slack\.com|discord(app)?\.com/api/webhooks' .
expect_no_match "no infrastructure or machine paths" \
  -RniE 'localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.|/home/|/Users/|C:\\' .
expect_no_match "personal email address absent" \
  -RniF 'jamestrichmond@gmail.com' .
expect_no_match "no private-repo paths or internal document codes" \
  -RniE 'AgentiCubed/A3|backend/app|frontend/src|docs/agentic3|docs/governance|boomerez|ADR-[0-9]|DR-[0-9]|WS-[0-9]' .
expect_no_match "no unfilled placeholders" \
  -RniE 'add before publishing|TBD|FIXME|replace me|your[-_ ]?(name|email|url)' .

# These two depend on your machine, so they are shown rather than auto-failed.
step "Machine-specific checks — read these hits yourself"
ME="$(whoami)"; HOST="$(hostname)"
MY_HITS="$(grep -RniF "$ME" . 2>/dev/null || true)"
HOST_HITS="$(grep -RniF "$HOST" . 2>/dev/null || true)"
if [ -n "$MY_HITS" ]; then
  printf '\n%s\n' "$MY_HITS"
  warn "Your username ('$ME') appears above. If any hit is a real path or account, STOP."
else
  pass "username ('$ME') does not appear"
fi
if [ -n "$HOST_HITS" ]; then
  printf '\n%s\n' "$HOST_HITS"
  warn "Your computer name ('$HOST') appears above. If any hit is real, STOP."
else
  pass "computer name does not appear"
fi

# ── 8. Assets, JSON, links ──────────────────────────────────────────────────
step "Assets and data"
EMBEDDED="$(find ./assets -type f -exec sh -c 'strings "$1" 2>/dev/null | grep -aiEq "mxfile|excalidraw" && echo "$1"' _ {} \; 2>/dev/null || true)"
[ -z "$EMBEDDED" ] || { printf '\n%s\n' "$EMBEDDED"; fail "Those assets carry embedded diagram source. Re-export with scene embedding OFF."; }
pass "no embedded diagram source in assets/"

BINARIES="$(find . -type f -exec file --mime {} \; 2>/dev/null | grep -v 'text/\|application/json' || true)"
if [ -n "$BINARIES" ]; then
  printf '\n%s\n' "$BINARIES"
  warn "Binary files found. Inspect each and check its metadata (exiftool) before continuing."
else
  pass "no binary files — nothing that can hide metadata"
fi

if [ "$HAVE_PY" -eq 1 ]; then
  while IFS= read -r f; do
    python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" \
      || fail "$f is not valid JSON."
  done < <(find . -name '*.json')
  pass "every JSON file parses"
  expect_empty "every JSON file carries the FABRICATED marker" \
    find . -name '*.json' -exec grep -L FABRICATED {} +
else
  warn "JSON checks skipped (no python3)"
fi

step "Markdown links"
if [ "$HAVE_PY" -eq 1 ]; then
  python3 - <<'PY' || fail "Broken relative links or heading anchors — see above."
import re, pathlib, urllib.parse, sys
root = pathlib.Path('.')
def slug(h): return re.sub(r'\s+','-',re.sub(r'[^\w\s-]','',h.strip().lower())).strip('-')
anchors = {p: {slug(m.group(1)) for m in re.finditer(r'^#{1,6}\s+(.*)$', p.read_text(), re.M)}
           for p in root.rglob('*.md')}
bad, n = [], 0
for md in root.rglob('*.md'):
    for m in re.finditer(r'\[[^\]]*\]\(([^)\s]+)\)', md.read_text()):
        t = m.group(1)
        if t.startswith(('http://', 'https://', 'mailto:')): continue
        n += 1
        p_, _, fr = t.partition('#')
        tgt = (md.parent / urllib.parse.unquote(p_)).resolve() if p_ else md.resolve()
        if not tgt.exists():
            bad.append(f"  {md}: missing file -> {t}"); continue
        rel = pathlib.Path(tgt).relative_to(root.resolve())
        if fr and tgt.suffix == '.md' and fr.lower() not in anchors.get(rel, set()):
            bad.append(f"  {md}: missing heading anchor -> {t}")
print(f"   checked {n} relative links")
if bad:
    print("\n".join(bad)); sys.exit(1)
PY
  pass "every relative link and heading anchor resolves"
else
  warn "link check skipped (no python3)"
fi

# ── 9. gitleaks (directory) ─────────────────────────────────────────────────
step "Secret scan"
if [ "$HAVE_GITLEAKS" -eq 1 ]; then
  gitleaks dir --no-banner --redact=100 . || fail "gitleaks found something. Do not continue."
  pass "gitleaks: zero findings"
else
  warn "SKIPPED — gitleaks is not installed. This is the one check with no substitute."
fi

# ── 10. Identity, then history ──────────────────────────────────────────────
step "Set the commit identity BEFORE committing"
info "Git stamps whatever identity it has into the commit, and that becomes"
info "public forever. This sets it explicitly for this folder only."
git init -q -b main
git config user.name  "$COMMIT_NAME"
git config user.email "$COMMIT_EMAIL"
pass "name:  $(git config --get user.name)"
pass "email: $(git config --get user.email)"
printf '\n'
read -r -p "   Is that the identity you want public forever? [yes/no] " ANSWER
case "$ANSWER" in
  yes|YES|y|Y) pass "identity confirmed by operator" ;;
  *) fail "Operator rejected the commit identity. Set GIT_EMAIL_OVERRIDE and rerun." ;;
esac

step "Stage everything and review it"
git add -A
git diff --cached --check || fail "Whitespace errors in the staged content."
pass "no whitespace errors"
printf '\n'
git diff --cached --stat | sed 's/^/   /'

step "Create exactly one commit"
git commit -q -m "$COMMIT_MESSAGE"
COUNT="$(git rev-list --count --all)"
[ "$COUNT" = "1" ] || fail "Expected exactly 1 commit, found $COUNT."
pass "exactly one commit"

git log --format='%an <%ae>%n%cn <%ce>' | sed 's/^/   /'
git log --format='%ae%n%ce' | grep -q '@users.noreply.github.com' \
  || warn "Commit identity is not a GitHub no-reply address — confirm that is deliberate."

expect_empty "no remote configured (Gate 6 adds it, not this script)" \
  git remote -v
[ -z "$(git status --porcelain)" ] || fail "Working tree is not clean after the commit."
pass "working tree clean"
# Captured into a variable rather than piped: under `set -o pipefail` a grep
# that matches nothing exits 1, which would make a CLEAN fsck look like a
# failure. Filtering in the shell keeps "no findings" as the success case.
FSCK_OUT="$(git fsck --full --no-reflogs --unreachable 2>&1 | grep -v '^Checking' || true)"
if [ -n "$FSCK_OUT" ]; then
  printf '\n%s\n' "$FSCK_OUT"
  fail "git fsck reported unexpected objects."
fi
pass "git fsck clean"

if [ "$HAVE_GITLEAKS" -eq 1 ]; then
  gitleaks git --no-banner --redact=100 . || fail "gitleaks found something in the commit history."
  pass "gitleaks history scan: zero findings"
fi

COMMIT_SHA="$(git rev-parse HEAD)"

# ── Done ────────────────────────────────────────────────────────────────────
printf '\n%s╔══════════════════════════════════════════════════════════╗%s\n' "$GRN" "$RST"
printf '%s║  GATE 5 COMPLETE — still nothing published                ║%s\n' "$GRN" "$RST"
printf '%s╚══════════════════════════════════════════════════════════╝%s\n' "$GRN" "$RST"
cat <<EOF

  Staging repo : $STAGE
  Commit       : $COMMIT_SHA
  Files        : $FILE_COUNT
  Identity     : $COMMIT_NAME <$COMMIT_EMAIL>

  Write that commit hash into the release record in
  docs/showcase/PUBLICATION-CONTROL-GATES.md (Gate 7).

  NEXT — Gate 6, and you do these by hand:
    1. On github.com, create AgentiCubed/agenticubed-showcase as a NEW,
       EMPTY, PRIVATE repository. Do not let GitHub add a README, a
       license, or a .gitignore — this tree already has all three.
    2. Then, from this folder:
         cd $STAGE
         git remote add origin git@github.com:AgentiCubed/agenticubed-showcase.git
         git push -u origin main
    3. Review how it renders on GitHub while it is still private.

  Do NOT make it public yet. That is Gate 8, and only you authorize it.

  If you need to change any content: delete this folder, fix showcase/ in
  the private repo, and run this script again. Never amend this commit.

EOF
