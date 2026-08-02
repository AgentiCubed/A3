# Boomerez Design Standard

Status: **draft** — criteria below are the scaffold baseline; refine as the
first app artifacts land.

## Artifact workflow

App HTML is produced in Claude chat as complete, self-contained artifacts and
dropped into `apps/<app-name>/`. Files under `apps/` are never created,
edited, or moved by hand or by repo tooling — fixes go back through chat and
arrive as a replacement artifact.

## Tokens

All shared visual values live in `packages/tokens/tokens.css` under the
`--bz-` prefix: color (light + dark schemes), typography, spacing, shape,
elevation, and motion (with reduced-motion support).

## Conformance criteria

- **CC-1 — Structure.** The repo keeps the canonical layout (`apps/`,
  `packages/`, `tools/`, `docs/`, `dist/`); build output only ever goes to
  `dist/`, which stays out of version control.
- **CC-2 — Tokens-only styling.** Apps style against `--bz-` tokens rather
  than repeating raw values; palette or scale changes happen once, in the
  tokens package.
- **CC-3 — Rubric lint.** Every shipped HTML artifact passes the
  `packages/earl-lint` rubric with zero errors. Enforced in CI alongside the
  W3C Nu validator (errors-only, still fatal on any error).
