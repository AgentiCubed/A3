# ADR 0005 — Lightweight SVG/CSS visualization + Mermaid source (MVP)

**Status:** Accepted · **Date:** 2026-06-25

## Context
The default stack names Recharts/Plotly for charts and Mermaid for dependency
graphs. The Phase-7 dashboards need: metric tiles, a CPM Gantt, a risk heat
matrix, an agent table, and a dependency graph.

## Decision
For the MVP, render charts/Gantt/risk-matrix with **pure SVG + CSS** (no chart
runtime dependency), and emit the dependency graph as **Mermaid source** (shown
in a `<pre class="mermaid">` block) plus an at-a-glance edge list — rather than
bundling a Mermaid/Recharts client renderer.

The visual logic (Gantt scaling, risk bucketing, Mermaid generation) lives in
pure, unit-tested helpers (`src/lib/metrics.ts`).

## Why this is a reasonable substitution
- **Robust CI/build.** Avoids Recharts/Plotly/Mermaid runtime peer-dependency and
  SSR friction under Next 15 / React 19, keeping `npm ci`, `tsc`, and `vitest`
  green without rendering heavy client libs.
- **Testable.** The pure helpers are exhaustively unit-tested; chart correctness
  doesn't depend on a third-party renderer.
- **Mermaid-compatible output.** We still produce Mermaid-format graph text, so a
  one-line upgrade renders it live; nothing about the data contract changes.
- **No data-model or API impact.** This is purely a presentation choice.

## Consequences / upgrade path
- Charts are functional but visually basic.
- To upgrade: add `recharts` (or Plotly) for richer charts and `mermaid` for live
  graph rendering in client components; the pure helpers and API stay unchanged.
  Tracked in `docs/issues/0005`.

## Alternatives considered
- Ship Recharts + Mermaid now — rejected for the MVP due to install/SSR/test
  fragility versus low presentation value at this stage.
