# Showcase publication checklist — PRIVATE

> **This file stays in the private repository. Do not copy it into the public
> showcase repo.** It is deliberately located outside `showcase/` so that copying
> `showcase/*` cannot pick it up by accident.

The publishable artifact is everything under `showcase/`. Nothing else.

---

## Part 1 — Decisions required before publication

Nine decisions. Six are quick; three are judgement calls. Nothing publishes until
all nine are settled.

### D1 — Positioning: social OS as thesis, governed loop as proof *(judgement call)*

**The tension.** The positioning specified for the showcase describes an "agentic
social operating system" spanning X, Threads, Bluesky, Mastodon, LinkedIn, Reddit,
and YouTube. What is actually built is a governed orchestration platform: plan →
approve → execute → evaluate → remediate → close. No social adapter exists.

**What was written.** The social operating layer is presented as the **thesis and
direction**; the governed loop is presented as **what works today**. The `Current
status` table in the README labels every social-layer item `Design`, and the
roadmap puts platform adapters in H2 with an explicit rationale for why they come
last. `demo/mock-platform-events.json` carries a `design_status` field saying the
same thing.

**Why this framing.** Claiming a social OS with no adapters would be checkable in
about ninety seconds by anyone technical, and at a conference full of technical
people that is a bad trade. Leading with a working governed substrate and an
argued reason the adapters come *last* is both true and a stronger position — the
sequencing argument is itself the differentiator.

**Your call.** Approve as written, or push harder toward the social framing and
accept that the status table has to keep telling the truth underneath it. Do not
resolve this by softening the status labels.

### D2 — Repository name

`agenticubed-showcase` was specified. Alternatives offered were `a3-showcase`,
`agenticubed-lab`, `agenticubed-public`.

Recommendation: **`agenticubed-showcase`** under the `AgentiCubed` org. It reads
as a deliberate public artifact, which is exactly what it is. `-lab` implies
experiments that are not there; `-public` invites "so where's the private one".

### D3 — Owner: org or personal account

Recommendation: **`AgentiCubed/agenticubed-showcase`**, then pin it on your
personal `JamesTRichmond` profile. Org ownership signals a project rather than a
side experiment; a profile pin gets it seen. You get both.

### D4 — License

Written as MIT for `demo/` and `assets/`, CC BY 4.0 for prose. Rationale: MIT is
the frictionless default for sample code and data, and CC BY on the prose means
someone lifting your architecture writeup owes you a credit line. Both files are
already in place.

Three mechanics that make the split hold up in public:

- GitHub's license detector reads a single root `LICENSE` file. With two
  licenses present, the repo header will show "View license" or just MIT —
  so the split must be declared where humans actually look: a short **License**
  section in the README stating exactly which paths carry which license.
- If `assets/` contains the AgentiCubed logo or wordmark, MIT invites reuse of
  the brand. Add one carve-out line: *"The AgentiCubed name and logo are not
  covered by these licenses and may not be used without permission."* Copyright
  licenses and trademark rights are separate things; say so explicitly.
- The strictly conventional license for fabricated demo *data* is CC0 rather
  than MIT. Optional — MIT is harmless here — but CC0 is what data publishers
  expect to see.

Alternative if you want it simpler: single Apache-2.0 for everything. Weaker
attribution on the prose, one fewer file.

### D5 — Contact details *(blocking)*

Four placeholders read `*(add before publishing)*`:

- `README.md` — "Connect at AI4": LinkedIn, X, email
- `docs/positioning.md` (renamed from ai4-positioning.md, 2026-09-05) — "Contact": LinkedIn, X, email

Decide what public-facing email you want on a repo that will be linked from
LinkedIn and a QR code. `jamestrichmond@gmail.com` is your personal address; a
project alias may age better. Publishing with placeholders still visible would be
worse than publishing with no contact section at all.

### D6 — Depth of the AI4 pitch

`docs/positioning.md` (renamed from ai4-positioning.md, 2026-09-05) includes a "Questions worth arguing about" section that
invites people to challenge the design, and states plainly that
governance-first-is-wrong is the most useful argument you could have. That is a
confident posture. It reads as strength to builders and as hedging to investors.

Confirm you want that framing. If the AI4 audience skews investor, that section
gets shorter and more declarative.

### D7 — Attribution of AI assistance

`docs/provenance.md` closes by stating that AI coding assistants are used
extensively, under the same governance the product describes. No model or vendor
is named.

This is honest, it is consistent with a governance-first pitch, and it preempts
the question rather than being caught by it. But it is a disclosure, and it is
yours to make. Confirm or cut.

### D8 — Naming GitHub in the provenance episode

`docs/provenance.md` names GitHub and the 2026-07-30 GitHub Models retirement.
The retirement is real and documented: end-of-life announced 2026-07-01, service
retired 2026-07-30, both in GitHub's own changelog.

Confirm you are comfortable naming a specific vendor in a public artifact — and
then anchor the claim to its primary source. `docs/provenance.md` must link the
announcement directly, so the episode rests on GitHub's own words rather than
your paraphrase:

- <https://github.blog/changelog/2026-07-01-github-models-is-being-fully-retired-on-july-30-2026/>
- <https://github.blog/changelog/2026-07-30-github-models-is-now-retired/>

The text stays factual and does not editorialize about GitHub. A named vendor
with a primary-source link is a citation; a named vendor without one reads as a
rumor.

### D9 — The QR code destination

The showcase README is the right landing page for a conference QR code: it
explains the project in the first paragraph and routes onward. Confirm, and
generate the QR against the final repo URL only *after* the name and owner are
locked.

Get the failure mode right, because it defines what actually has to be locked.
GitHub automatically redirects a **renamed repository's** URLs — web traffic and
git operations both — until some new repository claims the old name. What does
*not* hold is the owner: **renaming the org or user account** leaves the old
name claimable by anyone, and a claimed name plus a recreated repo path is a
hijack, not a 404. So the QR is not threatened by a repo rename; it is
threatened by an owner rename or a name squatter. Treat printed URLs as
immutable anyway — a redirect is a courtesy, not a contract.

---

## Part 2 — Pre-publication security checklist

Sections run in publication order, and each has its own moment: **A–C are ticked
before the public repository exists. R happens at repository creation and at the
flip to public. E happens after.** Within a section, top to bottom. (R7 and R8
*cannot* be ticked early even if you want to — on a free plan, secret scanning,
push protection, and branch protection exist only on public repositories.)

### A — Content audit

- [ ] **A1.** No API keys, tokens, or credentials of any kind. Verified by
      inspection and by a scan for high-entropy strings and known key prefixes.
- [ ] **A2.** No credential *references* either — no environment variable names
      that reveal which providers are wired up.
- [ ] **A3.** No OAuth, session, or authentication implementation detail.
- [ ] **A4.** No production prompts. No planner, executor, or evaluator prompt
      text, in whole or in excerpt.
- [ ] **A5.** No agent routing logic, model selection rules, or provider fallback
      ordering.
- [ ] **A6.** No real platform credentials, endpoints, or working adapters.
- [ ] **A7.** No user, customer, or client data — real, derived, sampled, or
      reconstructed from real data.
- [ ] **A8.** No non-public business strategy: no pricing, no commercial terms, no
      named prospects, no partnership discussions, no funding detail.
- [ ] **A9.** No exploitably specific security architecture. Invariants and
      boundaries only — no key management, no enforcement code paths, no
      thresholds, no dependency versions.
- [ ] **A10.** No deployment configuration: no compose files, no Dockerfiles, no
      infrastructure definitions, no hostnames, no ports, no cloud resources.
- [ ] **A11.** No private repository history. The public repo starts from a fresh
      `git init` with a single initial commit. **Never** publish by filtering the
      private repo's history — not because filtered objects leak (objects never
      pushed cannot be recovered from GitHub), but because filtering fails in
      practice: missed refs, missed blobs, one bad path spec. And the habit is
      fatal the day it gets applied to a repo that is *already* public, where
      forks, PR refs, and GitHub's caches keep every old object alive. Fresh init
      is the only approach with no failure modes.
- [ ] **A12.** No internal identifiers: no private issue or PR numbers, no
      internal file paths, no branch names, no CI job names, no internal document
      codes.
- [ ] **A13.** No screenshots. Diagrams only. (Console screenshots leak
      identifiers, route shapes, and account names more often than not.) And
      diagrams exported *clean*: draw.io/diagrams.net embeds the **full diagram
      XML** inside exported PNGs and SVGs unless "Include a copy of my diagram"
      is unchecked — including layers deleted from view. Excalidraw embeds scene
      data when "embed scene" is on. PDFs and images carry author and creator
      fields. Re-export every asset with embedding off; B7 verifies mechanically.
- [ ] **A14.** Every JSON file parses, and every one carries an explicit
      `FABRICATED` marker.

### B — Mechanical scan

Run once against `showcase/` while preparing, and run **again in Part 3 against
the staged tree** — the staged copy is what actually gets committed, and a scan
only counts when it ran against the exact bytes being published.

- [ ] **B1.** Secret scan — `gitleaks dir showcase/` (v8.19+; on older versions
      the legacy form is `gitleaks detect --no-git --source showcase/`), or
      equivalent. Zero findings.
- [ ] **B2.** Grep for secret shapes, case-insensitive where sensible. A hit on a
      *concept* is fine; a hit on a *value* is an automatic stop.

      ```bash
      grep -RniE 'api[_-]?key|secret|token|password|bearer|private[_-]?key|BEGIN.*PRIVATE' showcase/
      grep -RnE  'AKIA[0-9A-Z]|ASIA[0-9A-Z]|eyJ[A-Za-z0-9_-]{10}|xox[abprs]-|sk-ant-|sk-[A-Za-z0-9_-]{8}|ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|glpat-|AIza[0-9A-Za-z_-]|SG\.[A-Za-z0-9_-]{10}' showcase/
      ```

- [ ] **B3.** Grep for credential-bearing URIs and webhook URLs — a connection
      string with an `@` in it is a leaked credential regardless of what the
      surrounding prose claims:

      ```bash
      grep -RniE '(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqps?|smtps?|ftp)://[^ "]*@' showcase/
      grep -RniE 'hooks\.slack\.com|discord(app)?\.com/api/webhooks' showcase/
      ```

- [ ] **B4.** Grep for personal and infrastructure leakage. Hits on your public
      byline are expected; hits inside paths, configs, or examples are not:

      ```bash
      grep -RniE 'localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.|/home/|/Users/|C:\\' showcase/
      grep -RniF 'jamestrichmond@gmail.com' showcase/
      grep -RniF "$(whoami)" showcase/
      grep -RniF "$(hostname)" showcase/
      ```

- [ ] **B5.** Grep for private-repo leakage:

      ```bash
      grep -RniE 'AgentiCubed/A3|backend/app|frontend/src|docs/agentic3|docs/governance|boomerez|ADR-[0-9]|DR-[0-9]|WS-[0-9]' showcase/
      grep -RnE  '#[0-9]{1,4}' showcase/   # PR/issue refs; hex colors will false-positive — eyeball each hit
      ```

- [ ] **B6.** No symlinks — a symlink's stored target string is an internal-path
      leak that no content grep will ever see:

      ```bash
      find showcase/ -type l    # must print nothing
      ```

- [ ] **B7.** Asset metadata is clean. `exiftool -a -G1 -s` over everything in
      `assets/` shows no author, creator, company, or location fields worth
      keeping private, and no embedded diagram source survives:

      ```bash
      find showcase/assets -type f -exec sh -c 'strings "$1" | grep -aiEq "mxfile|excalidraw" && echo "EMBEDDED SOURCE: $1"' _ {} \;
      ```

      Any `EMBEDDED SOURCE` line means re-export per A13.
- [ ] **B8.** Every JSON file parses, and every one carries the `FABRICATED`
      marker:

      ```bash
      find showcase/ -name '*.json' -exec jq empty {} \;            # silence = pass
      find showcase/ -name '*.json' -exec grep -L FABRICATED {} +   # must print nothing
      ```

- [ ] **B9.** Every relative link in every Markdown file resolves (`lychee
      --offline showcase/`, or by hand). Rendered-README and Mermaid checks live
      in E1 — they cannot happen before a push exists.

### C — Human read-through

Mechanical scans do not catch judgement failures. Read every file end to end, in
one sitting, asking one question per pass:

- [ ] **C1.** *Would I be comfortable if a competitor read this line by line?*
- [ ] **C2.** *Would I be comfortable if a security researcher did?*
- [ ] **C3.** *Does anything here claim more than is true?* Cross-check every
      `Working` label in the README status table against something you have
      personally run.
- [ ] **C4.** *Does anything here name a real person, company, or account without
      their consent?* (GitHub is named per Part 1, D8 — a factual reference to a
      public, linked announcement.)
- [ ] **C5.** *Would this hand someone a blueprint?* If any single document would
      materially shorten a competent engineer's path to rebuilding the private
      implementation, cut it back.
- [ ] **C6.** *Does the provenance episode leak what A2 and A5 protect?* Naming
      the GitHub Models retirement necessarily reveals one provider dependency
      and the architectural response to losing it. That disclosure is deliberate
      — but read `docs/provenance.md` once against A2 and A5 specifically, and
      confirm it reveals nothing beyond the episode itself: no other providers,
      no fallback ordering, no routing logic.

### R — Repository configuration

*(Renamed from "D" so Part 1 decision numbers and Part 2 checklist numbers can
never be confused with each other.)*

- [ ] **R1.** Repository created **empty** and **private** — no auto-generated
      README, license, or `.gitignore`, since the tree supplies all three. It
      stays private until R6.
- [ ] **R2.** The staged tree contains only the contents of `showcase/`, and
      `PUBLICATION-CHECKLIST.md` is not among them. (Part 3, step 2 is where
      this gets verified by reading the file list.)
- [ ] **R3.** Description and topics set — e.g. `agentic-systems`,
      `ai-governance`, `agent-orchestration`, `llm-infrastructure`,
      `human-in-the-loop`.
- [ ] **R4.** Issues **enabled** (documentation corrections are welcome), wiki and
      projects **disabled**. Pull requests cannot be disabled on GitHub, so the
      README carries one line of contribution scope: corrections welcome; this is
      a documentation showcase, not an active codebase.
- [ ] **R5.** GitHub Actions **disabled** (Settings → Actions). The repo ships no
      workflows, and with Actions off, a future careless commit of one executes
      nothing.
- [ ] **R6.** Visibility flipped to **public** — the point of no return, taken
      only after every A, B, and C box is ticked and Part 3 is fully executed.
      Public is not the last step; it is the last *irreversible* step.
      Announcement (E2–E4) waits until R7–R9 and E1 are done.
- [ ] **R7.** Immediately after the flip: secret scanning **and** push protection
      enabled. Both are free on public repositories and unavailable or paywalled
      on private ones — which is why this box cannot precede R6. This is a
      backstop against *future* careless commits; the initial push was protected
      by B, not by this.
- [ ] **R8.** Branch protection (or a ruleset) on `main`: no force-push, no
      deletion. Same free-tier note as R7. The point is to make the panic reflex
      impossible: force-pushing to scrub a leak from a public repo does not work
      — forks, caches, and archives keep the objects — so the correct response to
      a leak is credential rotation and a fresh repo, and this rule keeps anyone
      from pretending otherwise.
- [ ] **R9.** Confirm the private `AgentiCubed/A3` repository is still
      **private**. Check this explicitly. It is the one mistake with no remedy.

### E — After publishing

- [ ] **E1.** Confirm the rendered README on github.com — Mermaid diagrams,
      tables, and links — from a logged-out browser session, before announcing
      anywhere.
- [ ] **E2.** Pin the repository on the `JamesTRichmond` profile. (Pinning an org
      repo on a personal profile works once you have contributed to it; the
      initial commit qualifies you.)
- [ ] **E3.** Generate the AI4 QR code against the final URL and test it on a
      phone that is not yours. Per D9: repo renames redirect, owner renames do
      not — the moment this prints, treat the owner name as frozen.
- [ ] **E4.** Add the link to LinkedIn and X profiles.
- [ ] **E5.** Set a reminder to re-check the status table after AI4. A stale
      `Working` label is worse than a `Design` one.

---

## Part 3 — Copy procedure

Once every A, B, and C box is ticked:

```bash
# 1. Stage a clean tree outside both repositories
mkdir -p ~/agenticubed-showcase
cp -R /path/to/agenticubed/showcase/. ~/agenticubed-showcase/
cd ~/agenticubed-showcase

# 2. Read the full file list — every path, in one sitting
find . -type f | sort

# 3. Remove OS droppings the copy may have carried
find . -name '.DS_Store' -delete
find . -name 'Thumbs.db' -delete

# 4. No symlinks, no git metadata — nested .git included
find . -type l          # must print nothing
find . -name '.git'     # must print nothing

# 5. Re-run B1–B8 against THIS directory — these are the bytes being published
gitleaks dir .
# ...then the B2–B5 greps and the B6–B8 checks, with path '.' instead of 'showcase/'

# 6. Identity before history — the commit embeds whatever git config holds, and
#    it is public forever via git log, the API, and .patch URLs. Copy the exact
#    noreply address from GitHub → Settings → Emails, and enable both
#    "Keep my email addresses private" and
#    "Block command line pushes that expose my email".
git init -b main
git config user.name  "James T. Richmond"
git config user.email "<ID>+JamesTRichmond@users.noreply.github.com"

# 7. Stage, then read every path once more
git add -A
git status

# 8. One commit. Optional but on-brand for a provenance project: sign it
#    (`git commit -S` with SSH signing configured) and it renders as Verified.
git commit -m "AgentiCubed public showcase"
git log --format='%an <%ae>%n%cn <%ce>'   # both lines must show the noreply address

# 9. Push to the NEW empty repo — still private; public happens at R6
git remote add origin git@github.com:AgentiCubed/agenticubed-showcase.git
git push -u origin main

# 10. Exactly one commit — locally, and on the github.com commits page
git log --oneline --all
```

`cp -R showcase/.` copies the directory's *contents*, dotfiles included, and
carries no `.git` only because the private repo's `.git` lives at its root — a
nested `.git` (a submodule, a stray experiment) would come along, which is what
step 4 exists to catch. Step 2 is the one people skip; do not skip it.
