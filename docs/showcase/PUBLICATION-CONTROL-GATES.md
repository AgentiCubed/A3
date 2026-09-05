# Showcase publication control gates — PRIVATE

> **PRIVATE CONTROL DOCUMENT.** This file stays in the private repository,
> outside `showcase/`. It must never be copied, linked, quoted, committed, or
> reproduced in the public showcase repository. Its absence from the staged tree
> is a mandatory release condition.

**Relationship to the other checklist.** `PUBLICATION-CHECKLIST.md` is the
*content* checklist — what must be true of the bytes being published. This file
is the *release-control* layer — the order operations happen in, who may
authorize what, what gets recorded, and what to do when something goes wrong.
Run them together: the gates below cite the checklist's item IDs rather than
restating them, so there is exactly one copy of every check.

**Fail-closed.** A blank decision, unresolved finding, remaining placeholder,
unexpected file, failed command, uncertain claim, or ambiguous license blocks
publication. Silence is not approval. Only James Richmond may authorize the
change from private to public.

---

## Publication states

| State | Meaning | External promotion allowed? |
|---|---|---|
| `SOURCE REVIEW` | Reviewing `showcase/` inside the private repository | No |
| `LOCAL STAGING` | Reviewing a clean local export with no remote | No |
| `PRIVATE PREFLIGHT` | New showcase repository exists privately on GitHub | No |
| `PUBLIC UNANNOUNCED` | Visibility is public; final smoke checks running | No |
| `RELEASED` | All gates passed and James authorized promotion | Yes |

---

## Publication boundary

- **Private source repository:** `AgentiCubed/A3`
- **Approved public source subtree:** `showcase/` — the only publishable material
- **Intended public repository:** `AgentiCubed/agenticubed-showcase`
- **Private control files:** this document and `PUBLICATION-CHECKLIST.md`

The public repository must not be a fork, branch, mirror, subtree split, bundle,
archive, filtered copy, or rewritten descendant of the private repository. It
must have no shared Git history, alternate object store, submodule relationship,
worktree relationship, or private remote.

---

## Gate 0 — Owner decisions

- [ ] All nine decisions in `PUBLICATION-CHECKLIST.md` Part 1 are resolved, with
      an explicit selection and a date. `PENDING` or conditional language blocks
      release.
- [ ] Resolved decisions are recorded in the decision log at the end of this file.

## Gate 1 — Private-source identity and visibility

- [ ] The working directory is the intended private A³ repository.
- [ ] `git remote -v` reviewed; no remote points at the intended public repo.
- [ ] `AgentiCubed/A3` verifies as **private**.
- [ ] This document and `PUBLICATION-CHECKLIST.md` are outside `showcase/`.
- [ ] No nested Git metadata or symlinks inside the tree:

      ```bash
      find showcase \( -name .git -o -name .gitmodules \) -print   # no output
      find showcase -type l -print                                 # no output
      ```

- [ ] Unrelated private work is untouched. Publication never stages, commits,
      cleans, resets, stashes, or rewrites anything outside `showcase/`.

## Gate 2 — Content, truth, privacy, licensing, IP

- [ ] `PUBLICATION-CHECKLIST.md` section **A** complete (A1–A14).
- [ ] Every file in the inventory has a specific public purpose. Nothing is
      included merely because it sat under `showcase/`.
- [ ] Every `Working` / `Implemented` / `Tested` / `Verified` claim is listed in
      the claim-to-evidence table below, with named evidence.
- [ ] Results produced by the private implementation are never presented as
      results produced by public code.
- [ ] Every file is covered by the license map below.
- [ ] Trademark exclusion is stated in the public tree.

**Scope corrections that apply to section A.** Several A-items are stated as
absolutes for *this* repository, which contains no executable code. They are
project boundary choices, not universal security standards, and they relax as
follows if the repository ever ships runnable code:

| Item | Correct reading |
|---|---|
| A2 | Environment-variable *names* are not credentials. A public `.env.example` with unmistakable placeholder values is fine. Withholding provider identity here is a proprietary-information choice. |
| A3 | Architecture-level authentication *boundaries* may be documented. What stays out: secrets, production endpoints, token values, exploitable weaknesses, key management, enforcement bypasses. |
| A4, A5 | Prompts, routing, fallback order, model selection, and thresholds are **protected implementation** — a trade-secret boundary, not a security requirement. |
| A9 (dependency versions) | If executable code is ever published, pin dependencies and commit the lockfile — reproducibility and vulnerability scanning need them. Today there is no code, so there is nothing to pin. |
| A10 | Deployment material is excluded because it crosses the private boundary. Generic, clearly non-production `localhost` examples are permissible where technically necessary. |
| A13 | Sanitized synthetic screenshots are permissible after metadata and visual-leak review. This repository chooses diagrams only. |
| A14 | The `FABRICATED` marker belongs on *fixtures and sample data only*. Never mark a schema, manifest, or configuration file as fabricated — that is its own falsehood. |
| C4 | The rule is not consent-before-naming. References to companies must be factual, sourced, non-confidential, neutral, and free of implied endorsement. Consent is required for private information, testimonials, and likenesses. |
| C5 | "Would this help a competent engineer?" fails as a test — every useful architecture document helps an engineer. The real test is the named protected-implementation list in A4/A5. Preserve enough substance to stay credible. |

## Gate 3 — Mechanical scans of the private source tree

- [ ] `PUBLICATION-CHECKLIST.md` section **B** complete (B1–B9).
- [ ] Tool versions recorded in the release record. Current Gitleaks syntax:

      ```bash
      gitleaks version
      gitleaks dir --verbose --redact=100 showcase/
      ```

      `gitleaks detect --no-git` is deprecated.
- [ ] Placeholder sweep is clean, or every remaining hit is recorded as BLOCKING:

      ```bash
      grep -RniE 'TODO|TBD|FIXME|add before publishing|replace me|example\.com|your[-_ ]?(name|email|url)|PENDING' showcase/
      ```

- [ ] B5's issue-reference grep is read as a *review queue*, not a failure list.
      Qualified patterns (`AgentiCubed/A3#123`, private repo URLs, internal
      document codes) are the real targets; bare `#123` will false-positive on
      hex colours and ordinary prose.
- [ ] No finding was suppressed or broadly allowlisted to obtain a clean result.
      Every accepted hit is in the exception log below.

## Gate 4 — Independent human read-through

- [x] `PUBLICATION-CHECKLIST.md` section **C** complete (C1–C6).

Read every public file end to end, in separate passes. Do not combine them.

- [x] **Pass A — skeptical technical reviewer.** Can a reader tell exactly what is
      implemented, private, synthetic, designed, and planned? Is every `Working`
      status supported?
- [x] **Pass B — security and privacy reviewer.** Does any combination of
      individually harmless details reveal a protected architecture, provider
      relationship, or identifier? Are synthetic examples unmistakably synthetic?
- [x] **Pass C — IP and licensing reviewer.** Would the owner knowingly grant
      every reuse right stated in the license map? Are trademarks excluded?
- [x] **Pass D — target reader.** Can an AI4 contact understand the project and
      its real status in under sixty seconds? Do the contact links work? Is it
      credible on mobile?

**Reviewer:** James Richmond (owner) **Date:** 2026-08-03 **Result:** **PASS** — all four passes

> **Gate 4 record.** Conducted against the rendered private preflight repository
> at the approved commit (`03ea8259`), not the source tree — the reviewed bytes
> are the publishable bytes.
>
> - **Pass A.** Every `Working` row in the status table was mapped to named
>   private tests. One evidence gap was found and repaired rather than waved
>   through: the "run against live model providers" claim had gone stale when
>   GitHub Models was retired (2026-07-30; nightly smoke red from 07-31).
>   PR #121 migrated both live workflows to the `gemini` adapter, and run
>   30783401657→30785033200 (2026-08-03) passed with the test **executed, not
>   skipped** — verified by reading the pytest summary, not the check badge.
> - **Pass B.** Full read of README, security-boundaries, provenance,
>   architecture, and both demo fixtures with the cross-document-leak question
>   held throughout. No findings. C6 re-checked against `provenance.md`
>   specifically: no second provider, no fallback ordering, no routing logic.
> - **Pass C.** Owner affirmed the CC BY 4.0 grant on prose and MIT on
>   `demo/` + `assets/`, including commercial adaptation with attribution;
>   trademark-exclusion sentence verified present; license-map paths verified
>   against the actual tree.
> - **Pass D.** Sixty-second mobile read passed — what it is, what works today,
>   and how to reach the owner were all answerable from memory. Every contact
>   link was opened by hand and confirmed to land on the intended profile.

## Gate 5 — Clean one-use local staging repository

> **GATE 5 PASSED — real run, 2026-08-02, James's machine, via
> `./scripts/showcase-gate5.sh`.** 22 files staged; no symlinks, nested git
> metadata, OS droppings, control documents, workflows, or binaries; all
> content scans clean; gitleaks 8.30.1 directory scan **and** git-history scan
> both zero findings; 51/51 links and heading anchors resolve; both JSON files
> parse with the `FABRICATED` marker; no whitespace errors; exactly one commit;
> author and committer both `James T. Richmond
> <170839886+JamesTRichmond@users.noreply.github.com>`; no remote configured;
> clean working tree; `git fsck` clean.
>
> **Approved commit:** `03ea8259aaaffd7ef0555cad9e48ef05c8d2b02e` — recorded in
> the Gate 7 release record below.
>
> **The staging folder is temporary and machine-local.** It lives under
> `/var/folders/.../agenticubed-showcase.j7TFDK` on James's Mac and is the exact
> thing Gate 6 pushes — do not delete it before Gate 6 is run, and do not run
> Gate 5 again unless content changes, since a second run produces a *different*
> commit that would need to replace this one everywhere it is referenced.
>
> *(Prior note, superseded: an earlier container-based rehearsal on 2026-08-02
> covered every check except gitleaks, which was unavailable in that
> environment. This entry is the real run and is authoritative.)*
> **One scan reads differently on your machine.** The `grep -RniF "$(whoami)"`
> check matched the ordinary English word "root" in the rehearsal, because the
> container user is `root`. On your machine `whoami` is your real username, so
> that check becomes meaningful rather than noisy — read its hits properly.

> **Run `./scripts/showcase-gate5.sh` rather than typing these by hand.** The
> script performs every step in this section, stops at the first failure, and
> never touches GitHub — no remote, no push, no repository, no visibility
> change. Typing twenty commands and eyeballing their output is how a check gets
> silently skipped; the commands below are the reference for what the script
> does and why.
>
> The script asks for confirmation twice — once on the file inventory, once on
> the commit identity — because those are the two decisions a script should
> never make for you.

Supersedes `PUBLICATION-CHECKLIST.md` Part 3 steps 1 and 6. A reusable
`mkdir -p ~/agenticubed-showcase` can silently merge into an existing directory;
`mktemp -d` cannot.

```bash
A3_SHOWCASE_SOURCE='/absolute/path/to/private-a3-repository/showcase'
A3_STAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agenticubed-showcase.XXXXXX")"

test -d "$A3_SHOWCASE_SOURCE"
test -n "$A3_STAGE_DIR"
test -z "$(find "$A3_STAGE_DIR" -mindepth 1 -print -quit)"   # must be empty

cp -R "$A3_SHOWCASE_SOURCE"/. "$A3_STAGE_DIR"/
cd "$A3_STAGE_DIR"
```

- [ ] The resolved staging path was read back and is not the private repo, a
      workspace root, or a home directory.
- [ ] Boundary verified in the staged copy:

      ```bash
      find . -type f -print | LC_ALL=C sort      # read every path
      find . -type l -print                      # no output
      find . \( -name .git -o -name .gitmodules \) -print   # no output
      ```

- [ ] Neither private control document is present.
- [ ] All Gate 3 scans re-run against the staged directory and passed. **These are
      the bytes being published; a scan of the source tree does not count.**
- [ ] **All content edits are finished before `git init`.** If anything must
      change after the commit, discard the staging directory and repeat Gate 5.
      Do not amend, reset, rebase, filter, or force-push the publication commit.
- [ ] Public-safe authorship confirmed *before* committing — Git history exposes
      author and committer identity permanently, via `git log`, the API, and
      `.patch` URLs:

      ```bash
      git init -b main
      git config user.name  "James T. Richmond"
      git config user.email "170839886+JamesTRichmond@users.noreply.github.com"
      git config --get user.email    # read it back
      ```

      The numeric prefix is the GitHub account ID for `JamesTRichmond`, resolved
      from the API on 2026-08-02. Confirm it against GitHub → Settings → Emails
      before use; if the account has since been renamed, the ID stays but the
      username part changes. Also enable **Keep my email addresses private** and
      **Block command line pushes that expose my email** while you are on that
      page — the second one turns a mistake here into a rejected push instead of
      a permanent public record.

- [ ] The **complete staged diff** reviewed, not merely `git status`:

      ```bash
      git add -A
      git diff --cached --check          # no whitespace errors
      git diff --cached --name-status
      git diff --cached --stat
      git diff --cached                  # read it
      ```

- [ ] Exactly one commit, clean tree, no remote, no unexpected objects:

      ```bash
      git commit -m "AgentiCubed public showcase"
      git rev-list --count --all         # must be 1
      git log --format='%an <%ae>%n%cn <%ce>'   # both lines = noreply address
      git remote -v                      # no output
      git status --short --branch        # clean
      gitleaks git --verbose --redact=100 .
      git fsck --full --no-reflogs --unreachable
      ```

- [ ] Commit hash recorded in the release record.

## Gate 6 — Private GitHub preflight

> **GATE 6 PASSED — real run, 2026-08-02.** `AgentiCubed/agenticubed-showcase`
> created empty and private, pushed from the Gate 5 staging commit
> (`03ea8259aaaffd7ef0555cad9e48ef05c8d2b02e`) over HTTPS (SSH was not
> configured on the operator's machine). Rendered view confirmed by James: all
> six Mermaid diagrams draw correctly, internal links resolve. Description and
> topics set. Issues enabled; Wiki and Projects disabled. Actions disabled.
> `AgentiCubed/A3` reconfirmed **Private** by direct inspection.
>
> **Noted, not blocking:** `AgentiCubed/A3` shows as "Private template" — the
> Template repository setting is on. Unrelated to this publication; flagged for
> James to review separately at Settings → General → Template repository.

- [ ] `PUBLICATION-CHECKLIST.md` **R1–R5** complete.
- [ ] **Note on R5.** The tree ships `.github/ISSUE_TEMPLATE/` (two issue forms).
      Issue templates are not workflows — R5's "the repo ships no workflows" is
      still true, and Actions should still be disabled. Confirm by reading the
      staged file list that `.github/workflows/` does **not** exist.
- [ ] Destination created **private**, empty, non-template, not a fork.
- [ ] Remote reviewed before pushing; push completed with **no force flag** and
      no bypassed security warning.
- [ ] Remote `main` commit hash matches the approved local hash.
- [ ] GitHub's rendered private view reviewed: README, every Mermaid diagram,
      tables, headings, code blocks, relative links, license mapping, description,
      topics, and the complete file tree against the approved manifest.
- [ ] No inherited or unexpected Actions runs, artifacts, releases, packages,
      Pages deployments, environments, secrets, variables, deploy keys, webhooks,
      or collaborators.
- [ ] Organization ownership, 2FA requirement, base permissions, and collaborator
      list reviewed. Only the minimum necessary people and apps have write access.
- [ ] Security-alert notifications reach an actively monitored account.
- [ ] Immediately before the flip, **both** repositories re-verified: `A3` still
      private; showcase private, not a fork, and a visibly different identity.

**Secret-scanning facts, stated correctly.** These are three separate things, not
one free toggle:

1. Secret scanning runs automatically on public repositories.
2. Account-level push protection for user pushes to public repositories is on by
   default.
3. *Repository-level* push protection is part of GitHub Secret Protection and may
   depend on the organization's plan.

## Gate 7 — Final release authorization

Publication is prohibited until every field is complete.

| Field | Value |
|---|---|
| Public repository | `AgentiCubed/agenticubed-showcase` |
| Approved commit hash | `03ea8259aaaffd7ef0555cad9e48ef05c8d2b02e` |
| Source-tree review date | 2026-08-02 (Gate 4) |
| Staging review date | 2026-08-02 — real run, `./scripts/showcase-gate5.sh`, operator's machine |
| Gitleaks version | 8.30.1 |
| Gitleaks directory result | 0 findings (scanned ~103.73 KB) |
| Gitleaks git-history result | 0 findings (1 commit scanned) |
| JSON validation result | 2/2 parse, both carry `FABRICATED` |
| Link validation result | 51/51 relative links + anchors resolve |
| Human-review result | **PASS** — Gate 4 passes A–D completed 2026-08-03 by James Richmond; record above |
| `AgentiCubed/A3` visibility verified | Yes — confirmed **Private** by James, 2026-08-02, github.com |
| Showcase private-preflight verified | Yes — Gate 6 complete, 2026-08-02 |
| Licensing decision approved | Yes — D4, MIT + CC BY 4.0 |
| Contact destinations approved | Yes — D5, LinkedIn + X live; email withheld by design |
| QR destination approved | `PENDING` — D9, generated only after Gate 9 |
| Unresolved exceptions | `NONE` — X-01 through X-07 all carry owner sign-off as of 2026-08-03 |

- [x] Every Gate 0–6 box complete (Gates 0–3 per the release record and exception
      log; Gate 4 per its record above; Gates 5–6 per their real-run records).
- [x] James Richmond has personally reviewed the final rendering and file tree
      (Gate 6 rendered-view check, 2026-08-02; Pass D mobile re-read, 2026-08-03).

**Release authorization:** `AUTHORIZED`
**Authorized by:** `James Richmond`
**Date and time:** `2026-09-05 HH:MM TZ`

Only James Richmond may change `NOT AUTHORIZED` to `AUTHORIZED`.

## Gate 8 — Public but unannounced

Change only the *showcase* repository's visibility. Never `AgentiCubed/A3`.

- [ ] `PUBLICATION-CHECKLIST.md` **R6–R9** and **E1** complete.
- [ ] Browser shows `AgentiCubed/agenticubed-showcase`, badge reads `Public`.
- [ ] `AgentiCubed/A3` re-confirmed `Private`.
- [ ] Logged-out smoke test: reachable without authentication; README, diagrams,
      tables, images, and links render; license and trademark boundary visible;
      correct on desktop and mobile; no permission-dependent asset appears.
- [ ] **Contact links verified by hand, from the logged-out session.** Both must
      open the intended profile:
      `https://www.linkedin.com/in/jamestrichmond` and
      `https://x.com/jamestrichmond`.
      A failed link is a release blocker, not permission to improvise another
      address. This check cannot be automated usefully — LinkedIn and X both
      refuse unauthenticated automated requests, so a scripted failure would not
      distinguish a wrong URL from a blocked bot. Open them yourself.
- [ ] A clean public clone contains exactly the approved commit and file tree, and
      requires no private submodule, package, registry, or credential.
- [ ] Branch protection configured so the panic reflex is impossible. Do not
      require an approval arrangement that makes a one-owner repository
      unmaintainable.

## Gate 9 — Release and promotion

- [ ] `PUBLICATION-CHECKLIST.md` **E2–E5** complete.
- [ ] QR generated from the final public URL, tested on two physical phones —
      one not signed into James's GitHub account — logged out, on cellular data,
      and at printed size and contrast.
- [ ] Repository description and topics are accurate and discoverable.
- [ ] Issues, security alerts, and contact channels are monitored.
- [ ] Status-table review scheduled immediately after AI4; full publication audit
      scheduled within thirty days.

## Gate 10 — Incident response and future updates

### Suspected credential exposure

1. Stop promotion and further pushes.
2. **Rotate the credential immediately.** Do not wait for history cleanup.
3. Record repository, path, commit, credential type, discovery time, and actions
   in a private incident record.
4. Assume already-public content was copied. Restricting visibility reduces
   *continuing* exposure; it does not undo exposure.
5. Do not rely on deleting the file or force-pushing rewritten history — forks,
   PR refs, and caches keep the objects.
6. Follow GitHub's sensitive-data removal procedure and contact Support for
   cached views and cross-references.
7. Re-scan related repositories, clones, artifacts, and publication materials.
8. Resume only through a new authorization record.

### Suspected personal or confidential exposure

Stop promotion, preserve a private record of what was exposed, identify every
surface that may hold it, obtain appropriate guidance when another person or
organization is involved, and do not promise complete removal until exposure
paths are verified.

### Incorrect or overstated public claim

Stop repeating it, correct it through a normal commit with a clear message, do
**not** rewrite public history to hide an ordinary mistake, update linked
conference and social materials, and record the correction.

### Rules for every future public update

- [ ] Develop public changes in the public repository, never inside the private
      A³ tree.
- [ ] Never add the private repository as a remote, submodule, subtree, package
      source, or workflow dependency.
- [ ] Review the complete staged diff before every commit.
- [ ] Run Gitleaks against changed files and public history before every push.
- [ ] Re-validate JSON, links, Mermaid, licenses, and fixture markers when
      affected.
- [ ] Never bypass push protection to meet a deadline.
- [ ] Reconfirm that every status claim is still current and every contact
      destination is still monitored.
- [ ] Never force-push or delete `main` as routine maintenance.

---

## Claim-to-evidence table

Every status label in the public README, and what backs it. The public reader
**cannot** inspect the evidence column — the implementation is private — which is
exactly why the README says so rather than implying public verifiability.

| Public claim | Evidence | Publicly inspectable? |
|---|---|---|
| Governed loop runs end to end | Private end-to-end lifecycle integration test | No |
| Strict plan contract validated at the boundary | Private schema + contract tests | No |
| Human approval gates on irreversible actions | Private approval-gate integration tests | No |
| Executor / evaluator separation | **Verified 2026-08-02 against source.** Three independent enforcement points: API boundary, dispatch (evaluator bound to task), and evaluation write. The "two enforcement points" claim in `security-boundaries.md` I6 is accurate and conservative. | No |
| Deterministic evaluation always runs; agent evaluation is added when an evaluator is assigned; verdicts combine | **Verified 2026-08-02 against source.** Corrected a prior overclaim — `architecture.md` §3.6 previously said both kinds were *required*. | No |
| Append-only audit, enforced at two layers | Private audit/immutability tests + DB trigger | No |
| Default-deny, scoped, expiring permissions | Private tool-runtime tests | No |
| Credential-by-reference with redaction | Private redaction + provider tests | No |
| Interchangeable, retirement-tolerant providers | Private provider adapter tests | No |
| Governance corpus, Phase 0 accepted | Private governance decision records | No |
| Operator console | Private end-to-end browser tests | No |
| Everything labelled `Design` | **No evidence claimed — that is what the label means** | n/a |

**Rule.** If a claim cannot be tied to a row here, narrow the claim or remove it.
Adding a row requires evidence that exists today, not evidence that is planned.

## License map

| Content class | Paths | License |
|---|---|---|
| Sample data and diagram sources | `demo/**`, `assets/**` | MIT — `LICENSE` |
| Prose documentation | `README.md`, `CONTRIBUTING.md`, `docs/**` | CC BY 4.0 — `LICENSE-DOCS.md` |
| AgentiCubed name, logo, brand identity | — | **Excluded from both grants** |
| The AgentiCubed implementation | not published | No license granted |

**Two things the owner should know, once.** CC BY 4.0 is not merely an
anti-plagiarism notice: it authorizes broad, irrevocable adaptation and
**commercial** reuse subject to attribution, and it cannot be withdrawn from
copies already received. That is the intended trade for a positioning document
whose value is being read. If it is not, the prose license is the thing to change
— before publication, not after. CC0 for the fabricated demo data is the
stricter convention and remains available; MIT is harmless and is what ships
unless asked otherwise.

## Decision log

| ID | Decision | Resolution | Approved by | Date |
|---|---|---|---|---|
| D1 | Positioning | Approve as written; add an above-the-fold non-connection statement | James Richmond | 2026-08-02 |
| D2 | Repository name | `agenticubed-showcase` | James Richmond | 2026-08-02 |
| D3 | Owner | `AgentiCubed` org, pinned on personal profile | James Richmond | 2026-08-02 |
| D4 | License | MIT for `demo/` + `assets/`, CC BY 4.0 for prose; no CC0 | James Richmond | 2026-08-02 |
| D5 | Contact | **Resolved.** LinkedIn `linkedin.com/in/jamestrichmond` and X `@jamestrichmond` ship. Personal Gmail never ships; the email line stays absent until a project alias exists, then is added in a later public commit. | James Richmond | 2026-08-02 |
| D6 | Pitch depth | Stands as written | James Richmond | 2026-08-02 |
| D7 | AI attribution | Disclosure kept; no vendor named | James Richmond | 2026-08-02 |
| D8 | Naming GitHub | Stands, with primary sources linked | James Richmond | 2026-08-02 |
| D9 | QR destination | README; generated only after name and owner lock | James Richmond | 2026-08-02 |
| D10 | Post-staging README divergence | A voice rewrite of `showcase/README.md` landed in source *after* the Gate 5 staging commit. Release the reviewed bytes (`03ea8259`) unchanged; the rewrite ships as the first post-release revision after a delta review. Same facts, same claims — tonal only, verified by diff. | James Richmond | 2026-08-03 |

## Exception log

Every intentional scan hit or accepted deviation. `None` is valid only after all
scans have run.

| ID | File and line | Finding | Why acceptable | Approved by | Date |
|---|---|---|---|---|---|
| X-01 | `showcase/**` (12 sites) | B2 matches on `secret` / `token` / `api key` | All conceptual prose, `_absent_by_design` entries, or `.gitignore` patterns. No values. | James Richmond | 2026-08-03 |
| X-02 | `showcase/docs/provenance.md` | Names GitHub and one retired provider dependency | Deliberate per D8; anchored to GitHub's own changelog. C6 re-run and passed: no other provider, no fallback ordering, no routing logic. | James Richmond | 2026-08-03 |
| X-03 | `README.md:10`, `README.md:82`, `security-boundaries.md:105`, `security-boundaries.md:125` | Placeholder sweep matches `TODO` / `PENDING` | Substring false positives: "Mas**todo**n", and the ordinary English "blocked **pending** a decision" / "de**pending** on". Verified with `grep -o`. | James Richmond | 2026-08-03 |
| X-04 | `showcase/demo/mock-platform-events.json` | Domain `example.invalid` | RFC 2606 reserved TLD — guaranteed never resolvable. Deliberately chosen over `example.com` so a fabricated federated handle can never be mistaken for a real one. | James Richmond | 2026-08-03 |
| X-05 | `showcase/README.md`, `showcase/docs/ai4-positioning.md` | ~~Four `*(add before publishing)*` placeholders~~ | **RESOLVED 2026-08-02.** LinkedIn and X supplied by the owner and inserted in both files. Zero placeholders remain. Email line stays absent per D5 until an alias exists. | James Richmond | 2026-08-02 |
| X-06 | `showcase/README.md`, `showcase/docs/ai4-positioning.md` | Two public contact identifiers ship: `linkedin.com/in/jamestrichmond`, `x.com/jamestrichmond` | Approved public destinations per D5. These are the **only** approved personal identifiers; B4 must still fail on any other. Both are intentionally public professional profiles. | James Richmond | 2026-08-02 |
| X-07 | *(process)* `AgentiCubed/A3` repository settings | Gate 6's "disable Actions" step was applied to **A3** instead of the showcase repo. All A3 workflows queued without executing from ~2026-08-02T19:48Z until re-enable on 2026-08-03; PRs #119 and #121 merged inside that window with no CI run. | Detected during Pass A evidence verification (a dispatched run sat queued with zero jobs). Owner re-enabled Actions on A3 2026-08-03; the live smoke went green immediately after, confirming health. Showcase repo Actions remains disabled per R5. No content or publication artifact was affected. | James Richmond | 2026-08-03 |

---

## Final rule

The purpose of these gates is not to prove publication is risk-free. It is to
ensure publication is deliberate, truthful, reproducible where claimed, legally
intelligible, and bounded to exactly the material James Richmond chose to
release.

When uncertainty remains, publication stops.
