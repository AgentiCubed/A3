# Issue 0012 — Artifact ergonomics and in-app downloads

**Status:** DRAFT · **Source:** `docs/MVP-ITERATION-TODO.md` B5, E3  
**Suggested labels:** `type:enhancement`, `area:backend`, `area:frontend`, `track:quality`

## Summary
Make produced artifacts easier to find and consume with human-readable names,
project-named folders, and direct download access in the UI.

## Problem
Artifacts are currently harder to browse than they should be because storage and
retrieval are optimized for internal identifiers rather than operator workflow.

## Desired outcome
Operators should be able to locate and download project outputs from the product
without resorting to container copy commands or opaque file naming.

## Acceptance criteria
- [ ] Artifact file names are human-readable and stable for the same logical
      output type.
- [ ] Per-project artifact storage uses a project-meaningful folder name rather
      than only an internal UUID.
- [ ] The UI lists artifacts for a project and supports direct downloads.
- [ ] Download and path handling are covered by tests that prevent traversal or
      cross-project leakage.

## Dependencies
- Artifact metadata updates in the backend.
- Frontend artifact browser and download actions.

## Security and risk notes
- Artifact downloads must enforce project-scoped authorization.
- File naming must not allow path injection or overwrite collisions.
