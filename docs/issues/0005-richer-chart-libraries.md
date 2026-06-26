# Issue 0005 — Upgrade dashboards to Recharts/Plotly + live Mermaid

**Status:** PARTIALLY RESOLVED (auth) (2026-06-26) · **Opened:** 2026-06-25 · **Phase:** 7

## Resolution (auth — the security-relevant half)
The dashboard no longer needs `?token=` in the URL. A `/login` page posts to a
Next route handler (`/api/session`) that exchanges credentials for an access token
and stores it in an **httpOnly** cookie (`ac_token`, `sameSite=lax`,
`secure` in prod). The dashboard reads the cookie via `next/headers`; `?token=`
remains only as a scripted/demo fallback. This removes tokens from URLs/referrers.

## Deferred (intentional, per ADR-0005)
Richer chart rendering (Recharts/Plotly, live Mermaid) stays deferred: the MVP
uses lightweight SVG/CSS + Mermaid *source* on purpose to keep CI/build/test
robust under Next 15 / React 19 (see ADR-0005). The pure helpers and data
contracts are unchanged, so this is a drop-in upgrade when desired.

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
