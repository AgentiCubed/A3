# PROC-0001 — Git Workflow Procedure

**Type:** Procedure  
**Version:** 1.0  
**Authority:** [POL-0001 Gate Workflow](POL-0001-gate-workflow.md)  
**Status:** Active

---

## Purpose

This Procedure defines the branch naming, commit, pull request, and merge conventions for `AgentiCubed/agenticubed`. These are implementation choices, not constitutional requirements. They may be updated through an authorized PR without governance amendment.

---

## Branch Naming

| Branch | Purpose |
|---|---|
| `main` | Protected. Receives only merged PRs. Never pushed to directly. |
| `copilot/<descriptor>` | Agent-authored branches for Copilot-executed work |
| `<username>/<descriptor>` | Human-authored branches |

Branch descriptors should be lowercase, hyphen-separated, and descriptive enough to identify the work without requiring context (e.g., `copilot/fix-ci-server-teardown`, not `copilot/fix1`).

---

## Commit Messages

Commits shall use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short description>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

Examples:
- `fix(ci): tolerate already-stopped server in readiness smoke test teardown`
- `docs(adr): ADR-0006 explicit lint targets decision`
- `feat(api): add project milestone endpoint`

The short description:
- uses imperative mood ("add", "fix", "remove", not "added", "fixed");
- does not end with a period;
- is complete enough to identify the change without reading the diff.

---

## Pull Requests

All changes to `main` shall be made through a pull request.

**Every PR description shall include:**

- a summary of what changed and why;
- the issue(s) it addresses (e.g., `Closes #5`);
- for governance/constitutional changes: a reference to the governing instrument;
- for CI or infrastructure changes: verification evidence (test results, smoke test output);
- explicit non-goals (what was intentionally not changed).

PRs for governance or constitutional documents shall receive independent review before merge, consistent with [STD-0001](STD-0001-context-complete-reviews.md).

PRs may be opened as drafts while work is in progress. A draft PR shall not be merged.

---

## Verification Before Merge

Before merging:

| Change type | Required verification |
|---|---|
| Backend code | `make check` green (ruff + black + pytest) |
| Frontend code | `make check` green (eslint + vitest) |
| CI workflow | At minimum a review pass; ideally a triggered CI run |
| Governance/constitutional documents | Independent review satisfying STD-0001 |
| Documentation only | Relative links verified; no constitutional text modified |

---

## Merge Method

Pull requests shall be merged using GitHub's **merge commit** or **squash merge**:

- **Merge commit** — preserves the full commit history of the branch; preferred for feature work with meaningful commit sequence.
- **Squash merge** — collapses branch commits into a single commit on `main`; preferred for small fixes or cleanup where intermediate commits add no information.

Rebase merge is not the default. If used, it must not rewrite commits already pushed to a shared branch.

---

## Prohibited Actions

- No direct push to `main`.
- No force-push to shared branches.
- No rewriting of commits already present in a merged PR.
- No merge of a draft PR.
- No merge of a PR with failing required checks.

---

## Governance and Constitutional Changes

PRs that add or modify content under `docs/governance/constitution/` shall:

1. identify the constitutional deficiency or amendment purpose;
2. include independent review evidence (separate from the author);
3. reference the applicable amendment procedure ([DR-0001](../decisions/DR-0001-Constitutional-Amendment-Procedure.md));
4. receive explicit ratification from the Principal before merge.

PRs that add or modify other governance documents (decisions, playbook, ratification records) shall be reviewed for consistency with the Constitution and with existing governance instruments before merge.
