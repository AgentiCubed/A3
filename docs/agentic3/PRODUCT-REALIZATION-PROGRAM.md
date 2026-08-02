# Agentic3 Product-Realization Program

**Status:** Proposed; effective only after
[DR-0006](../governance/decisions/DR-0006-Product-Realization-Canon.md) is
ratified and merged  
**Governing issue:** [#106](https://github.com/AgentiCubed/A3/issues/106)  
**Baseline:** `AgentiCubed/A3@7061cd6d130d7863bf66bc12173c7896373da5b5`  
**Registry:** [WORKSTREAM-REGISTRY.json](WORKSTREAM-REGISTRY.json)

## 1. Purpose

This program is the delivery spine for work that turns the shipped A3 platform
and the Agentic3 architecture into an inspectable, artifact-producing system.
It coordinates parallel contributors without making an agent, branch, issue, or
conversation authoritative.

The repository on `main` is the durable coordination surface. Cubit is the
initial program steward, not the source of authority. Principal decisions,
governing instruments, and merged evidence remain authoritative.

## 2. Authority and precedence

This program is subordinate to, in order:

1. the Constitution and ratified amendments;
2. governance decisions and active playbook instruments;
3. adopted Agentic3 architecture and Runtime baselines;
4. accepted Architecture Decision Records;
5. this program and its registry;
6. workstream designs, issues, PRs, and implementations.

A lower layer cannot silently replace or contradict a higher layer. A conflict
must be recorded, reviewed, and resolved by an authorized supersession decision.
Unmerged branches, model output, screenshots, chat transcripts, and issue text
are proposals or evidence, never canon by themselves.

Architecture v2 remains the canonical architecture consolidation target. This
program governs realization order, ownership, integration, and evidence; it
does not promote the draft, redefine its engines, or retro-specify the shipped
platform.

## 3. Canonical position

A contributor determines current position by reading, in order:

1. [ARCHITECTURE-v2.md](ARCHITECTURE-v2.md);
2. [IMPLEMENTATION-BLUEPRINT.md](IMPLEMENTATION-BLUEPRINT.md);
3. this program;
4. [WORKSTREAM-REGISTRY.json](WORKSTREAM-REGISTRY.json);
5. the governing issue and active PR for the selected workstream.

The registry state vocabulary is:

- `proposed`: shaped but not authorized;
- `authorized`: bounded work is approved but not started;
- `active`: one identified branch owns the current increment;
- `blocked`: a named condition prevents legitimate progress;
- `implemented`: code or documentation exists but verification is incomplete;
- `verified`: required evidence passed;
- `released`: merged and available in the declared release boundary;
- `superseded`: replaced through an explicit linked decision.

Only merged updates may advance canonical state. CI evidence is required for a
`verified` claim; process uptime or executor self-attestation is insufficient.

## 4. Parallel-work convergence contract

Before starting a PR, every contributor must record:

- canon version and baseline commit;
- workstream ID and bounded increment;
- affected paths and contract surfaces;
- dependency state;
- compatibility or supersession impact;
- expected evidence and rollback;
- active-PR collision check.

Exact path ownership is exclusive while a workstream is `active`. Overlapping
or newly discovered ownership requires reconciliation before either PR changes
the shared contract. A later branch rebases or updates from current `main`; it
does not overwrite the merged decision. Generated output may not rewrite
governance, architecture, migrations, audit history, or another workstream's
owned contract as a side effect.

A contract change is compatible only when existing consumers remain valid or an
expand-and-contract transition is recorded. Breaking changes require a version,
consumer inventory, migration and rollback plan, and authorized decision.
Corrections append or supersede; they do not erase the prior record.

## 5. Program sequence

The registry is authoritative for dependencies. The intended delivery arc is:

1. `GOV-01`: canon and enforcement;
2. `RT-01`: Blueprint Phase 1 event-ledger vertical slice;
3. `EXP-01`: truthful intake, provider readiness, health, and diagnostics;
4. `PLAN-01`: validated plans and inspectable task graph;
5. `TRACE-01`: human and technical execution evidence;
6. `ART-01`: artifact contracts, versions, previews, and export;
7. `CTRL-01`: approvals, controls, evaluation, and bounded remediation;
8. `3D-01`: deterministic procedural scene and verified GLB proof.

Runtime and product-experience increments remain independently releasable.
Their first integration checkpoint is the versioned event/artifact boundary,
not a shared rewrite.

## 6. Required evidence

Every workstream increment supplies:

- happy-path and boundary-denial tests appropriate to the change;
- organization isolation for every query or endpoint;
- offline mock-provider proof for normal CI;
- migration upgrade and downgrade evidence when schema changes;
- contract compatibility evidence;
- user-visible artifact or trace evidence where applicable;
- exact CI conclusion before claiming verification;
- docs and ADR impact plus explicit non-goals.

Significant architecture work also requires the STD-0002 traceability packet and
an independent, context-complete review.

## 7. Collision and drift response

When work conflicts with the registry:

1. stop writes to the contested path or contract;
2. preserve both proposals and identify the common baseline;
3. classify the difference as compatible extension, sequencing conflict, or
   semantic contradiction;
4. update the owning workstream or obtain a supersession decision;
5. resume from the reconciled `main` state.

The validator detects structural drift. Human and independent review remain
responsible for semantic conflicts.

## 8. Reopening conditions

Reopen DR-0006 if this program blocks legitimate independent work, fails to
prevent silent contract replacement, diverges from a higher-layer instrument,
creates ownership deadlocks, or cannot reconstruct why a delivered capability
was authorized and accepted.
