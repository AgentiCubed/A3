# FR-0001 — Constitutional Release Process Failures

## Status

Contained and verified through [PR #7](https://github.com/AgentiCubed/agenticubed/pull/7), main CI run #12, and release [`constitution-v1.0-a0001`](https://github.com/AgentiCubed/agenticubed/releases/tag/constitution-v1.0-a0001).

## Context

Repository: [`AgentiCubed/agenticubed`](https://github.com/AgentiCubed/agenticubed)

Workstream: publication of [Constitution v1.0](../constitution/Constitution-v1.0.md) and [Amendment A-0001](../constitution/Amendment-A-0001.md)

Relevant artifacts:

- [Constitution v1.0](../constitution/Constitution-v1.0.md)
- [PR #7](https://github.com/AgentiCubed/agenticubed/pull/7)
- merge commit [`e31c44460f2d6416cb2c2b4398c6b3a658147f29`](https://github.com/AgentiCubed/agenticubed/commit/e31c44460f2d6416cb2c2b4398c6b3a658147f29)
- release [`constitution-v1.0-a0001`](https://github.com/AgentiCubed/agenticubed/releases/tag/constitution-v1.0-a0001)

## Observed Failures

### F1 — Governance files were committed directly to `main`

The initial Constitution, Ratification Record, Commentary, and amendment procedure were created through GitHub's web editor and committed directly to `main` instead of entering through a feature branch and pull request.

### F2 — Branch and commit context were repeatedly confused

GitHub pages showed a branch,