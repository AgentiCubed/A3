# @boomerez/earl-lint

Rubric linter enforcing design standard criterion **CC-3**: every shipped
HTML artifact passes `rubric.json` with zero errors.

```sh
python3 packages/earl-lint/earl_lint.py apps          # lint all app HTML
python3 packages/earl-lint/earl_lint.py path/to.html  # lint one file
```

Exit code is non-zero when any rubric rule fails, so CI fails on errors.
Rules live in `rubric.json` and map to checks implemented in `earl_lint.py`;
the starter rubric covers baseline structure and accessibility (doctype,
`lang`, title, viewport, `img` alt text) plus token linkage. Extend the
rubric as the design standard grows.
