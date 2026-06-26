# Issue 0003 — CPM models all dependency types as finish-to-start

**Status:** RESOLVED (2026-06-26) · **Opened:** 2026-06-25 · **Phase:** 3

## Resolution
`app/scheduling/critical_path.py` now models all four PMI relations. Each task
carries separate start/finish variables; per-edge constraints (FS/SS/FF/SF with
lag) drive the forward/backward pass via `_forward_lower_bound` /
`_backward_upper_bound`. `task_service.compute_timeline` threads
`dependency_type` into the engine. Verified by `test_critical_path` (one fixture
per relation; FS results unchanged).

## What is incomplete
`TaskDependency.dependency_type` accepts all four PMI relations
(`finish_to_start`, `start_to_start`, `finish_to_finish`, `start_to_finish`),
and the value is persisted and returned by the API/graph. But the Critical Path
engine (`app/scheduling/critical_path.py`) currently models **every** dependency
as finish-to-start with an optional lag. SS/FF/SF relations therefore schedule
as if they were FS.

## Why it is incomplete
FS is the dominant relation (>90% of real plans) and keeps the forward/backward
pass simple and exhaustively testable for the MVP. Full multi-relation CPM needs
per-relation constraints on both start and finish variables.

## Proposed implementation
Generalize the pass to track each task's start and finish as separate timeline
variables and apply per-edge constraints:
- FS: `succ.start >= pred.finish + lag`
- SS: `succ.start >= pred.start + lag`
- FF: `succ.finish >= pred.finish + lag`
- SF: `succ.finish >= pred.start + lag`
Then derive ES/EF/LS/LF from the constrained variables. Add a test matrix with
one fixture per relation. Estimated: ~half a day.

## Dependencies
None. Pure-domain change in `app/scheduling`; no schema or API change (the field
already exists).

## Security implications
None.
