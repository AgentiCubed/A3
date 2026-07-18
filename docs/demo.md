# Governed objective-to-close demonstration

`app/seed/demo.py` takes one objective through the governed runtime: a durable
plan draft, explicit approval of exact plan bytes, task materialization, one
project start, execution and evaluation, automatic remediation, acceptance, and
closeout.

This is an offline, reproducible orchestration proof. `MockProvider` produces
planning and agent responses deterministically; it does not represent live model
reasoning. The pandas computation, permission checks, matplotlib rendering,
artifact bytes, hashes, database records, and audit trail are real.

## What it does

Project: *"Market brief: Widget X regional demand."*

1. **Objective and agents** — creates an organization, owner, planner, executor,
   and a separate evaluator. The objective carries a transparent demo fixture
   marker so `MockProvider` returns the same reviewable plan every time.
2. **Draft and approval** — generates and stores a two-task `research → deliver`
   plan, then explicitly approves its exact version and SHA-256 hash. Approval
   atomically creates the task graph, assignments, remediation limits, and
   persisted rubrics.
3. **One governed start** — validates the approved materialization, changes the
   project from `planning` to `active`, records the approved plan metadata in the
   start audit, and schedules the dependency chain once.
4. **Permissioned analysis** — the research task invokes the granted
   `analysis.summary_stats` tool. That tool performs the real pandas computation
   over values `120, 95, 140, 110`; the deterministic agent response only requests
   and reports the tool result.
5. **Evaluation and automatic remediation** — the deliver task's first
   deterministic response intentionally omits `DEMO_ACCEPTED`. Its persisted
   `contains_all` rubric rejects the output, the remediation policy selects an
   automatic add-context retry, and the next response includes the token only
   after receiving the recorded evaluation gap.
6. **Real artifacts** — Python/matplotlib renders `demand-chart.png`, and the
   accepted deliver output becomes `market-brief.md`. Both are stored through the
   real artifact store with content hashes. When `Rscript` is available, the R
   worker adds an optional statistics cross-check; R is not acceptance-critical.
7. **Acceptance and closeout** — project acceptance verifies the accepted output
   and both artifacts. The project closes without an unmet-criteria override, and
   the closeout report is generated from persisted history.

## Run it

Against a live database (Docker stack up, migrations applied):

```bash
make demo          # python -m app.seed.demo  → prints the closeout markdown
```

Or programmatically: `build_and_run_demo(session, store=..., now=...)` returns the
plan approval hash and status, materialized tasks, evaluations, remediation and
tool-invocation evidence, artifact hashes, acceptance result, close audit, and
closeout report. `tests/integration/test_demo.py` verifies that evidence, and CI
runs it in the named **Governed objective-to-close proof** step.

## What it proves

- A reviewed plan, not hand-built tasks, controls materialization and execution.
- One governed start advances the approved graph, and acceptance must pass before
  close.
- Executor/evaluator separation, persisted rubrics, permissioned tools, automatic
  remediation, and immutable execution/evaluation history all engage.
- pandas/matplotlib analysis and visualization, artifact storage, and persistence
  are real.
- Planning and agent text are deterministic `MockProvider` fixtures. The demo
  does not prove the quality, judgment, or reliability of a live language model.
