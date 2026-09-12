# MVP Iteration TODO — output quality, transparency, and project intake

Direction set by the Principal on 2026-08-01 after the first hands-on MVP
session: the loop works end to end; the product now needs (1) reliable
live-model runs, (2) dramatically better deliverable quality, (3) full
visibility into what the system thinks and does, and (4) a project-intake
experience that confirms understanding before anything runs.

Owners: **C** = Claude (Executor), **J** = James (Principal). Ordered
within each section by dependency, not difficulty.

## A. Unblock and harden live runs

- [x] **A1 — OBSOLETE (superseded by the provider migration):** this item
      predates GitHub Models' 2026-07-30 retirement. The live credential is
      now `GEMINI_API_KEY` (Google AI Studio), already configured and
      proven by a live run. Verify any time with
      `docker compose exec api printenv GEMINI_API_KEY | cut -c1-6`.
- [x] **A2 (C):** actionable provider errors — DONE: each
      `ProviderErrorCategory` maps to allowlisted human copy; execution
      and plan diagnostics store `operator_message` (human + machine
      form); the dashboard humanizes bare machine diagnostics. Machine
      form remains parseable via `parse_provider_diagnostic`.
- [x] **A3 (C):** credential preflight — DONE: `POST /api/v1/providers/preflight`
      and `GET /api/v1/providers`; home-page Provider readiness panel;
      `python -m app.seed.live_agents --verify` for non-destructive CLI
      setup checks.
- [ ] **A4 (C):** failure UX — a blocked/escalated task must show its
      error and a "retry with fixes" path on the dashboard, not hide it in
      the database.
- [x] **A5 (C):** rate-limit resilience — DONE except model fallback:
      the adapter retries 429s honoring Retry-After (capped 15s) before
      surfacing a failure, dispatch paces retries (2s, 10s when
      rate-limited) instead of re-firing instantly, and the attempt budget
      was raised to 120s so in-adapter backoff fits inside it. Optional
      model fallback remains open.

## B. Deliverable quality (code)

- [ ] **B1 (C):** planner prompt overhaul — derive a multi-task plan with
      per-task deliverable specs, acceptance criteria, and dependencies
      from the actual objective (no more generic research→deliver pair
      when the objective warrants more).
- [ ] **B2 (C):** executor context enrichment — objective, plan, prior
      task outputs, and a deliverable template flow into every execution
      prompt (predecessor handoff exists; widen it).
- [ ] **B3 (C):** draft → self-review → revise loop per task before the
      independent evaluation, with the iteration count governed by a
      project setting (see D-board control #22).
- [ ] **B4 (C):** live evaluator rubrics — grade against
      objective-derived criteria, not just `non_empty`.
- [ ] **B5 (C):** artifact ergonomics — human-readable file names, a
      per-project folder named after the project (not a UUID), and
      download buttons in the UI (replace `docker compose cp`).
- [ ] **B6 (C):** per-task model routing — strong model for
      planning/writing, fast model for mechanical steps; configurable.
- [ ] **B7 (C, candidate — needs governance):** real research capability
      (web/tool access for agents) — requires an authorization boundary
      decision before any implementation; do not build silently.

## C. Transparency — running stream of thought, logged and queryable

- [ ] **C1 (C):** persist full execution transcripts — every prompt sent
      and response received per attempt (secrets redacted), stored with
      the execution record.
- [ ] **C2 (C):** transcript viewer — one scrollable page per project with
      every plan draft, prompt, response, evaluation, and remediation in
      chronological order; browser Ctrl+F/Cmd+F works across all of it.
- [ ] **C3 (C):** execution timeline — per-task live status with model,
      provider, token counts, durations; task titles (not the generic
      "task") and deep links in the Live activity feed.
- [ ] **C4 (C):** one-click log export — `project-log.md` containing the
      full run history for offline analysis.
- [ ] **C5 (C):** fix the "Reconnecting…" live-feed indicator and the
      stale metric tiles (auto-refresh on terminal events).

## D. Project intake redesign — understand, correct, refine, then create

- [ ] **D1 (C):** "understanding" step — after name + objective are
      entered, the system presents its own summary of what it believes the
      objectives, deliverables, assumptions, and out-of-scope items are —
      **before** the project is created.
- [ ] **D2 (C):** correction loop — the user edits or comments on that
      understanding; the system restates; repeat until the user confirms.
      The confirmed understanding becomes the plan input and is stored in
      the audit trail.
- [ ] **D3 (C+J):** replace the single objective textbox with a **toggle
      board**: ~25 controls (switches and sliders) with built-in
      suggestions, each showing **immediate feedback** — before Create is
      clicked — on how it will influence the end product. Starter set of
      25 for the Principal to review, veto, and extend:
      1. Deliverable format (report / brief / slides / code / dataset)
      2. Depth (slider: overview ↔ exhaustive)
      3. Target audience (general / executive / technical / academic)
      4. Tone (formal ↔ conversational slider)
      5. Length target (slider, with page/word preview)
      6. Include executive summary (switch)
      7. Include charts/visuals (switch + how many slider)
      8. Include data tables (switch)
      9. Research breadth (slider: focused ↔ wide)
      10. Citation/source strictness (off / loose / strict)
      11. Creativity vs precision (slider)
      12. Task granularity (slider: few big tasks ↔ many small tasks)
      13. Evaluation strictness (slider — feeds evaluator rubric)
      14. Max self-revision iterations per task (slider — feeds B3)
      15. Max automatic remediations before human gate (slider)
      16. Model tier (fast/free ↔ strongest available)
      17. Language and reading level
      18. Structure template (auto / user-supplied outline)
      19. Jargon level (avoid ↔ embrace domain terms)
      20. Risk posture (conservative claims ↔ bold projections)
      21. Include open-questions section (switch)
      22. Include methodology/appendix section (switch)
      23. Deadline urgency (slider — influences plan sizing)
      24. Acceptance criteria editor (prefilled, user-adjustable)
      25. Human approval gates (every task / milestones only / start+close)
- [ ] **D4 (C):** live influence preview — a side panel that updates as
      controls change: predicted plan shape, estimated tasks, estimated
      model calls, and a sample paragraph in the chosen tone/depth.
- [ ] **D5 (J):** aesthetic pass — Principal-led list of visual and layout
      improvements, delivered as annotated screenshots; C implements.

## E. Paper cuts already found in first use

- [x] **E1 (C):** DONE via silent refresh, which is strictly better than a
      longer access token: the frontend now stores both tokens in httpOnly
      cookies and the proxy renews the pair transparently on expiry, so
      sessions last REFRESH_TOKEN_TTL_SECONDS (14 days) while a stolen
      access token still dies within ACCESS_TOKEN_TTL_SECONDS. Both TTLs
      remain config-driven and now reach the frontend container in prod
      compose.
- [x] **E2 (C):** DONE — "Sign in to create a project." links to /login.
- [ ] **E3 (C):** artifacts browser in the UI (list + download per
      project) — supersedes the `docker compose cp` workaround.
- [x] **E4 (C):** DONE — `suppressHydrationWarning` on root `<html>` and
      `<body>` to silence extension-injected attribute mismatches.

## F. Process

- [ ] **F1 (J):** review this list — especially the 25 controls in D3 —
      veto, amend, extend; priorities land in the order J sets.
- [ ] **F2 (C):** implement in small PR-sized slices, each verified in the
      Principal's environment before the next begins; quality bar: every
      slice leaves `make demo`, CI, and the live path green.
- [ ] **F3 (parked, unchanged):** governance track — Codex review-findings
      repairs and Agentic³ Phase 1 — resumes on the Principal's word; this
      product track does not silently supersede it.
