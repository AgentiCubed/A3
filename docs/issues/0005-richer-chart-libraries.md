# Issue 0005 — Upgrade dashboards to Recharts/Plotly + live Mermaid

**Status:** Open · **Opened:** 2026-06-25 · **Phase:** 7

## What is incomplete
Dashboards render with pure SVG/CSS and emit Mermaid graph *source* rather than a
live-rendered diagram (see ADR-0005). The richer libraries named in the default
stack (Recharts/Plotly, a live Mermaid renderer) are not yet wired.

## Why it is incomplete
Kept the MVP's CI/build robust under Next 15 / React 19 and the test suite free of
heavy client-render dependencies. Presentation value did not justify the install/
SSR risk at this stage.

## Proposed implementation
- Add `recharts` (client components) for the status breakdown + agent metric
  charts; keep the pure helpers as the data source.
- Add `mermaid` and a small client component that renders `<pre class="mermaid">`
  blocks on mount (dynamic import) — the source is already generated and tested.
- Add a real login UI / session cookie so dashboards no longer need `?token=`.

## Dependencies
`recharts`, `mermaid` npm packages; an auth/session mechanism for the frontend.

## Security implications
Replace the `?token=` query-param auth (MVP convenience) with an httpOnly session
cookie so tokens don't land in URLs/referrers/logs.
