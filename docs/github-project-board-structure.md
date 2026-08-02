# GitHub project board structure for the monorepo

This repository is a multi-surface product monorepo: backend API/services,
frontend UI, worker/runtime execution, deployment/ops, and governance/docs. A
single GitHub Project can work well if it uses explicit fields and saved views
instead of separate boards per app.

## Recommended fields

| Field | Type | Purpose |
| --- | --- | --- |
| Status | single select | `Inbox`, `Ready`, `In progress`, `Blocked`, `In review`, `Done` |
| Priority | single select | `P0`, `P1`, `P2`, `P3` |
| Size | single select | `XS`, `S`, `M`, `L`, `XL` |
| Track | single select | `Live runs`, `Quality`, `Transparency`, `Intake`, `Platform`, `Governance` |
| Area | single select | `backend`, `frontend`, `workers`, `deploy/infra`, `docs/governance`, `cross-cutting` |
| Type | single select | `bug`, `enhancement`, `epic`, `chore`, `docs` |
| Target release | text | Milestone or release train |
| Depends on | text | Blocking issue references |
| Evidence | text | Test, workflow, or demo proof expected before close |

## Default views

### 1. Roadmap
- Group by `Track`
- Sort by `Priority`, then `Size`
- Filter out `Done`
- Use for principal-level ordering and dependency review

### 2. Current iteration
- Board layout grouped by `Status`
- Filter to `Priority` in `P0`, `P1`
- Show `Area`, `Track`, and `Depends on`
- Use for active delivery work

### 3. Backend / runtime
- Table filtered to `Area` in `backend`, `workers`
- Show `Evidence`, `Depends on`, `Target release`
- Use for API, orchestration, and execution changes

### 4. Frontend / UX
- Board or table filtered to `Area = frontend`
- Show `Track`, `Priority`, `Evidence`
- Use for dashboard, intake, and artifact-browser work

### 5. Cross-cutting epics
- Table filtered to `Type = epic`
- Show `Area`, `Track`, `Depends on`, `Target release`
- Use to manage initiatives that split into backend/frontend child issues

## Workflow guidance

1. Open large initiatives as `type:epic` workstreams and link focused child
   issues beneath them.
2. Keep each implementation issue scoped to one shippable slice even when it
   touches more than one app.
3. Do not move an item to `Done` until the issue's acceptance criteria and
   recorded evidence are both satisfied.
4. Use `Blocked` only when another issue or an external decision is the active
   constraint; capture the blocker in `Depends on`.
5. Prefer labels for stable taxonomy (`area:*`, `type:*`, `track:*`) and project
   fields for stateful planning (`Status`, `Priority`, `Size`).
