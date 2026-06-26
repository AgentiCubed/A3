# End-to-end demonstration

`app/seed/demo.py` builds and runs a complete project through the entire control
loop — **Plan → Assign → Execute → Evaluate → Identify Gaps → Remediate →
Re-execute** — and then produces a closeout report.

## What it does

Project: *"Market brief: Widget X regional demand."*

1. **Org + agents** — creates an organization, an owner, and four agents
   (Researcher, Writer, Analyst, and a **separate** Evaluator).
2. **Plan** — creates the project (CPM recommended from its signals),
   requirements, a milestone, four tasks, and their dependencies.
3. **Assign** — capability-checked assignment of each task to an agent.
4. **Execute + Evaluate** — research, brief, and analysis tasks run through the
   MockProvider, each graded by a deterministic rubric **and** the separate
   evaluator agent (executor ≠ evaluator).
5. **Real analysis + visualization** — the **Python worker** (pandas) computes
   summary statistics over a sample regional dataset and the matplotlib worker
   renders a bar chart, stored as an **Artifact** (the visualization). If `Rscript`
   is installed, the **R worker** cross-checks the statistics.
6. **Deliberate failure → remediation** — the chart-render task carries a
   `[[FAIL]]` marker; its first attempt fails and the task escalates. A
   remediation is applied (the offending input is cleaned, a Decision is logged),
   the task returns to READY, and the re-run **completes**.
7. **Closeout** — a final report is generated (outcome, failures & remediation,
   deliverables, risks, decisions, metrics) and the project is **closed**.

## Run it

Against a live database (Docker stack up, migrations applied):

```bash
make demo          # python -m app.seed.demo  → prints the closeout markdown
```

Or programmatically: `build_and_run_demo(session, store=..., now=...)` returns a
summary dict (used by `tests/integration/test_demo.py`, which asserts the project
closed, exactly one deliberate failure, a remediation, a real PNG deliverable, and
the computed statistics).

## What it proves

- The full closed loop runs end-to-end on real persistence.
- Executor/evaluator separation, deterministic rubrics, remediation, and human-
  free auto-remediation all engage.
- The analysis/visualization workers are **real** (pandas/matplotlib, and R when
  present) — not mocks.
- Every step is audited and the execution/evaluation history is immutable.
