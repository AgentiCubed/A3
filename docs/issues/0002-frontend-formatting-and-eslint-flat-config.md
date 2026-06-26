# Issue 0002 — Frontend: Prettier deferred; ESLint on legacy config

**Status:** Open · **Opened:** 2026-06-25 · **Phase:** 1

## What is incomplete
1. **Prettier** is not wired into the frontend. The roadmap's Phase 1 criterion
   named `eslint + prettier`; only ESLint (`eslint-config-next`) is configured.
2. ESLint uses the legacy `.eslintrc.json` (`next/core-web-vitals` +
   `next/typescript`) rather than ESLint 9 flat config (`eslint.config.mjs`).
   `next lint` supports the legacy file, so this works today but is deprecated.

## Why it is incomplete
Phase 1 prioritized a verified, runnable scaffold (component tests + typecheck
green) over formatter polish. ESLint already enforces style via the Next preset,
so Prettier was non-blocking.

## Proposed resolution
- Add `prettier` + `eslint-config-prettier`, a `format` script, and a
  `prettier --check` step in `make frontend-lint`.
- Migrate to `eslint.config.mjs` flat config when bumping to the Next flat-config
  defaults. Target: Phase 7 (UI build-out) or earlier if it causes friction.

## Dependencies
None blocking. Pure dev-tooling change.

## Security implications
None.
