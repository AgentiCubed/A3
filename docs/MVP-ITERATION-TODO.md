# MVP Iteration TODO — output quality, transparency, and project intake

Direction set by the Principal on 2026-08-01 after the first hands-on MVP
session: the loop works end to end; the product now needs (1) reliable
live-model runs, (2) dramatically better deliverable quality, (3) full
visibility into what the system thinks and does, and (4) a project-intake
experience that confirms understanding before anything runs.

Owners: **C** = Claude (Executor), **J** = James (Principal). Ordered
within each section by dependency, not difficulty.

## A. Unblock and harden live runs

- [ ] **A1 (J, now):** finish the token repair — add the new token to
      `.env` (`echo "GITHUB_MODELS_TOKEN=<paste>" >> .env`), run
      `docker compose up -d`, verify with
      `docker compose exec api printenv GITHUB_MODELS_TOKEN | cut -c1-14`
      → must print `github_pat_` + 3 chars, nothing doubled.
- [ ] **A2 (C):** actionable provider errors — map
      `invalid_request/status=none` class failures to human messages
      ("credential missing or malformed", "model ID unknown", "rate
      limited — retry after X") in the stored task error and the UI.
- [ ] **A3 (C):** credential preflight — a cheap provider ping surfaced on
      the dashboard (and a CLI `--verify` on the live-agents seed) so a bad
      token is caught before a project fails.
- [ ] **A4 (C):** failure UX — a blocked/escalated task must show its
      error and a "retry with fixes" path on the dashboard, not hide it in
      the database.
- [ ] **A5 (C):** rate-limit resilience — exponential backoff + optional
      model fallback for 429s on the free tier.

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

- [ ] **E1 (C):** lengthen local session lifetime (15-minute logouts are
      hostile on a personal machine); config-driven.
- [ ] **E2 (C):** "Sign in to create a project." becomes a link to /login.
- [ ] **E3 (C):** artifacts browser in the UI (list + download per
      project) — supersedes the `docker compose cp` workaround.
- [ ] **E4 (C):** hydration-warning hygiene on / and /login (extension
      attribute noise suppressed via suppressHydrationWarning on body).

## F. Process

- [ ] **F1 (J):** review this list — especially the 25 controls in D3 —
      veto, amend, extend; priorities land in the order J sets.
- [ ] **F2 (C):** implement in small PR-sized slices, each verified in the
      Principal's environment before the next begins; quality bar: every
      slice leaves `make demo`, CI, and the live path green.
- [ ] **F3 (parked, unchanged):** governance track — Codex review-findings
      repairs and Agentic³ Phase 1 — resumes on the Principal's word; this
      product track does not silently supersede it.
