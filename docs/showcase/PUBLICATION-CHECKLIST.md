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
the frictionless default for sample data, and CC BY on the prose means someone
lifting your architecture writeup owes you a credit line. Both files are already
in place.

Alternative if you want it simpler: single Apache-2.0 for everything. Weaker
attribution on the prose, one fewer file.

### D5 — Contact details *(blocking)*

Four placeholders read `*(add before publishing)*`:

- `README.md` — "Connect at AI4": LinkedIn, X, email
- `docs/ai4-positioning.md` — "Contact": LinkedIn, X, email

Decide what public-facing email you want on a repo that will be linked from
LinkedIn and a QR code. `jamestrichmond@gmail.com` is your personal address; a
project alias may age better. Publishing with placeholders still visible would be
worse than publishing with no contact section at all.

### D6 — Depth of the AI4 pitch

`docs/ai4-positioning.md` includes a "Questions worth arguing about" section that
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
The retirement is public and announced, and the episode is the strongest story in
the repository — it is real evidence of an architectural response to a real event.

Confirm you are comfortable naming a specific vendor in a public artifact. The
text is factual and does not editorialize about GitHub, but it is a named vendor.

### D9 — The QR code destination

The showcase README is the right landing page for a conference QR code: it
explains the project in the first paragraph and routes onward. Confirm, and
generate the QR against the final repo URL only *after* the name and owner are
locked — a QR pointing at a renamed repo is a dead card in someone's pocket.

---

## Part 2 — Pre-publication security checklist

Run top to bottom. Every box gets ticked before the repo is created, not after.

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
      `git init` with a single initial commit. **Never** push a filtered branch of
      the private repo — filtered history is recoverable more often than people
      expect.
- [ ] **A12.** No internal identifiers: no private issue or PR numbers, no
      internal file paths, no branch names, no CI job names, no internal document
      codes.
- [ ] **A13.** No screenshots. Diagrams only. (Console screenshots leak
      identifiers, route shapes, and account names more often than not.)
- [ ] **A14.** Every JSON file parses, and every one carries an explicit
      `FABRICATED` marker.

### B — Mechanical scan

Run against the `showcase/` tree before creating the public repo:

- [ ] **B1.** Secret scan — `gitleaks detect --no-git --source showcase/`, or
      equivalent. Zero findings.
- [ ] **B2.** Grep for high-risk substrings, case-insensitive: `api_key`, `apikey`,
      `secret`, `token`, `password`, `bearer`, `private_key`, `BEGIN.*PRIVATE`,
      `AQ\.`, `sk-`, `ghp_`, `github_pat_`, `gho_`, `ghu_`, `ghs_`, `ghr_`,
      `AIza`. Every hit must be an intentional mention of the *concept*, never a value.
- [ ] **B3.** Grep for personal and infrastructure leakage: `localhost`, `127.0.0.1`,
      `/home/`, `/Users/`, `C:\`, your real email, machine names.
- [ ] **B4.** Grep for private-repo leakage: `AgentiCubed/A3`, `backend/app`,
      `frontend/src`, `docs/agentic3`, `docs/governance`, `boomerez`, `DR-00`,
      `ADR-00`, `WS-`, `#1`–`#999` PR references.
- [ ] **B5.** `git log --all --oneline` in the new public repo shows exactly one
      commit.
- [ ] **B6.** Every JSON file parses cleanly.
- [ ] **B7.** Every relative link in every Markdown file resolves.
- [ ] **B8.** Every Mermaid block renders on GitHub (check the rendered README
      *after* the first push, before announcing).
- [ ] **B9.** A `.gitignore` file is present in `showcase/` and covers at least
      `.DS_Store`, `Thumbs.db`, and other OS-generated artifacts. Confirm with
      `git status` after `git add -A` that no stray files are staged.

### C — Human read-through

Mechanical scans do not catch judgement failures. Read every file end to end, in
one sitting, asking one question per pass:

- [ ] **C1.** *Would I be comfortable if a competitor read this line by line?*
- [ ] **C2.** *Would I be comfortable if a security researcher did?*
- [ ] **C3.** *Does anything here claim more than is true?* Cross-check every
      `Working` label in the README status table against something you have
      personally run.
- [ ] **C4.** *Does anything here name a real person, company, or account without
      their consent?* (GitHub is named per D8 — a factual reference to a public
      announcement.)
- [ ] **C5.** *Would this hand someone a blueprint?* If any single document would
      materially shorten a competent engineer's path to rebuilding the private
      implementation, cut it back.

### D — Repository configuration

- [ ] **D1.** Repository created **empty** — no auto-generated README, license, or
      `.gitignore`, since the tree supplies all three.
- [ ] **D2.** Fresh `git init` in a clean directory containing only the contents
      of `showcase/`. Confirm `PUBLICATION-CHECKLIST.md` is not among them.
- [ ] **D3.** Visibility set to **public** only as the final action, after
      everything above.
- [ ] **D4.** Description and topics set — e.g. `agentic-systems`, `ai-governance`,
      `agent-orchestration`, `llm-infrastructure`, `human-in-the-loop`.
- [ ] **D5.** Issues **enabled** (documentation corrections are welcome), wiki and
      projects **disabled** (nothing to put in them).
- [ ] **D6.** Secret scanning and push protection enabled — free on public repos,
      and a genuine backstop against a future careless commit.
- [ ] **D7.** Branch protection on `main`: no force-push, no deletion, and
      **require a pull request before merging** (creates an audit trail even
      when you are the sole maintainer). If CI is ever connected, also require
      status checks. History rewrites on a public repo are how private data
      becomes permanently archived.
- [ ] **D8.** Confirm the private `AgentiCubed/A3` repository is still **private**.
      Check this explicitly. It is the one mistake with no remedy.

### E — After publishing

- [ ] **E1.** Pin the repository on the `JamesTRichmond` profile.
- [ ] **E2.** Confirm the rendered README on github.com — Mermaid diagrams, tables,
      and links — from a logged-out browser session.
- [ ] **E3.** Generate the AI4 QR code against the final URL and test it on a phone
      that is not yours.
- [ ] **E4.** Add the link to LinkedIn and X profiles.
- [ ] **E5.** Set a reminder to re-check the status table after AI4. A stale
      `Working` label is worse than a `Design` one.

---

## Part 3 — Copy procedure

Once every box above is ticked:

```bash
# 1. Stage a clean tree outside both repositories
mkdir -p ~/agenticubed-showcase
cp -R /path/to/agenticubed/showcase/. ~/agenticubed-showcase/

# 2. Confirm what you are about to publish — read this list in full
cd ~/agenticubed-showcase
find . -type f | sort

# 3. Confirm no private-repo git metadata came along
ls -la          # there must be no .git directory yet

# 4. Fresh history, single commit
git init
git add -A
git status      # read every path once more before committing
git commit -m "AgentiCubed public showcase"

# 5. Push to the NEW empty public repo, then verify
git remote add origin git@github.com:AgentiCubed/agenticubed-showcase.git
git branch -M main
git push -u origin main
git log --oneline --all    # must show exactly one commit
```

`cp -R showcase/.` copies the contents, not the directory, and carries no `.git`.
Step 3 is the one people skip; do not skip it.
