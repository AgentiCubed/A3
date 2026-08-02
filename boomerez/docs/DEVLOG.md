# Boomerez Dev Log

## 2026-08-02 — Repo scaffold

Stood up the initial Boomerez structure:

- `apps/mode-studio/` — empty landing zone for source HTML. Artifacts arrive
  from Claude chat complete; nothing in this repo creates or edits app HTML.
- `packages/tokens/` — shared CSS design tokens (`--bz-` custom properties,
  light/dark schemes, reduced-motion support). Starter values, provisional.
- `packages/earl-lint/` — rubric linter enforcing design standard criterion
  CC-3; rules in `rubric.json`, stdlib-only Python, non-zero exit on errors.
- `tools/` — `build.py` (copies apps + tokens into `dist/`, writes a build
  manifest) and `run_tests.py` (structure, tokens, rubric, .gitignore, and
  earl-lint execution checks).
- `docs/DESIGN-STANDARD.md` — draft standard with conformance criteria
  CC-1 (structure), CC-2 (tokens-only styling), CC-3 (rubric lint).
- CI: ported the Static Site CI workflow from `JamesTRichmond/LordAinz`,
  specifically the hardened errors-only HTML validation variant
  (`vnu --skip-non-html --errors-only`, commit `9af74bc` — not the earlier
  relaxed `aeddeb7` version). Adapted: validates HTML under `apps/`, runs
  `tools/run_tests.py`, rubric-lints via earl-lint, builds `dist/`, and
  fails on any error. HTML validation and rubric lint self-skip only while
  `apps/` contains zero HTML files.
- Added MIT LICENSE, README with CI badge (slug assumes the standalone home
  is `AgentiCubed/boomerez` — update if it lands elsewhere), and .gitignore
  covering `/dist/`, `node_modules`, `.env*`, and audio/video media.

Scaffold note: this tree was assembled on a branch of `AgentiCubed/A3`
(`boomerez/` subdirectory) because the session couldn't create a standalone
repo; the tree is fully self-contained and ready to extract with
`git subtree split` (or a plain copy) into its own repository — at which
point the workflow in `.github/workflows/ci.yml` goes live.
