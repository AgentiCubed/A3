# Boomerez

[![Static Site CI](https://github.com/AgentiCubed/boomerez/actions/workflows/ci.yml/badge.svg)](https://github.com/AgentiCubed/boomerez/actions/workflows/ci.yml)

Static app workspace. App HTML arrives from Claude chat as complete artifacts
and is dropped into `apps/<app-name>/` — it is **never** created, edited, or
moved by hand (or by tooling) inside this repo.

## Structure

```
apps/mode-studio/     Source HTML artifacts land here (do not hand-edit)
packages/tokens/      Shared CSS design tokens
packages/earl-lint/   Rubric linter (design standard criterion CC-3)
tools/                Build + test scripts
docs/                 Design standard, dev log
dist/                 Build output (gitignored)
```

## CI

`.github/workflows/ci.yml` — Static Site CI, ported from
[JamesTRichmond/LordAinz](https://github.com/JamesTRichmond/LordAinz)
(the hardened, errors-only HTML validation variant). On every push and PR it:

1. Verifies scaffold-critical files exist.
2. Runs the test suite: `python3 tools/run_tests.py`.
3. Validates all HTML under `apps/` with the W3C Nu validator
   (`vnu --skip-non-html --errors-only`) — fails on any error.
4. Runs the earl-lint rubric linter over `apps/` (CC-3).
5. Builds `dist/` and uploads it as an artifact.

> Badge note: the badge above assumes this tree's standalone home is
> `AgentiCubed/boomerez`; update the slug if the repo lands elsewhere.

## Local commands

```sh
python3 tools/run_tests.py    # run the test suite
python3 tools/build.py        # build into dist/
python3 packages/earl-lint/earl_lint.py apps   # rubric-lint app HTML
```

All tooling is Python 3 stdlib only — no install step.

## License

[MIT](LICENSE)
