# DR-0006 — Product-Realization Canon

## Registration block

- **Stable ID:** DR-0006
- **Version:** 0.1.0
- **Ratification status:** **Proposed — not yet ratified.** Per
  [DR-0001](DR-0001-Constitutional-Amendment-Procedure.md)'s principle, the
  operative act is the Principal's explicit ratification; Executor agreement,
  merge of this file, or CI success is not ratification. The
  [Product-Realization Program](../../agentic3/PRODUCT-REALIZATION-PROGRAM.md)
  is effective only after this decision is ratified and merged.
- **Scope:** coordination of product-realization work in this repository —
  precedence, workstream registry semantics, and convergence duties. No
  product behavior, schema, migration, provider configuration, deployment,
  or 3D implementation.
- **Governing gate:** issue
  [#106](https://github.com/AgentiCubed/A3/issues/106), authorized by the
  Principal instruction in the governing executor session on 2026-08-02
  ("gate 1 approved; sign-off is granted for gate 2"), under
  [POL-0001](../playbook/POL-0001-gate-workflow.md).

## Purpose

Establish one Principal-ratifiable product-realization canon that reconciles
the shipped A3 platform, Agentic³ Architecture v2, the Implementation
Blueprint, and the experience/artifact/3D program, so that parallel
contributors can determine their workstream, owned paths, dependencies,
compatibility duties, and evidence state without conversational memory.

## Context

1. The shipped platform (`backend/`, `frontend/`) and the Agentic³
   architecture drafts evolved in parallel; no single instrument coordinated
   realization order, path ownership, or contract compatibility.
2. Phase 0 is accepted
   ([DR-0005](DR-0005-Phase-0-Acceptance.md)) and
   [ARCHITECTURE-v2.md](../../agentic3/ARCHITECTURE-v2.md) is the single
   canonical consolidation target, still draft.
3. Unmerged branches, model output, and session memory are not repository
   truth ([PRECEDENCE-AND-RETENTION](../../agentic3/PRECEDENCE-AND-RETENTION.md)
   §1.1); a canon must therefore live on `main` as durable artifacts.

## Decision

1. **Canon artifacts.** The product-realization canon comprises the
   [Product-Realization Program](../../agentic3/PRODUCT-REALIZATION-PROGRAM.md)
   and the machine-readable
   [WORKSTREAM-REGISTRY.json](../../agentic3/WORKSTREAM-REGISTRY.json),
   enforced by
   [`scripts/check_product_canon.py`](../../../scripts/check_product_canon.py)
   and the hermetic tests in
   [`backend/tests/unit/test_product_canon.py`](../../../backend/tests/unit/test_product_canon.py).
2. **Baseline pin.** The governing repository baseline is
   `AgentiCubed/A3@7061cd6d130d7863bf66bc12173c7896373da5b5` (`main`). Canon
   claims are evaluated against that commit and its merged successors, never
   against unmerged proposals.
3. **Precedence and supersession.** The program's precedence order (program
   §2) is adopted: Constitution and amendments; governance decisions and
   active playbook instruments; adopted architecture and Runtime baselines;
   accepted ADRs; the program and registry; then workstream designs, issues,
   PRs, and implementations. A lower layer cannot silently replace or
   contradict a higher layer (the
   [Upward Compatibility Rule](../playbook/STD-0002-traceable-architecture-reviews.md));
   replacement of a canonical contract requires an explicit, evidence-backed
   supersession decision, and corrections append or supersede — they never
   erase the prior record.
4. **Registry contract.** Every workstream carries a stable ID, title, owner
   role, state from the registry's `allowed_states` vocabulary,
   dependencies, owned paths, contract surfaces, acceptance evidence, and a
   collision policy. Exact path ownership is exclusive while a workstream is
   `active`. Only merged updates advance canonical state; a `verified` claim
   requires CI evidence.
5. **Enforcement.** The validator must reject duplicate workstream IDs,
   unknown or self-referential dependencies, dependency cycles, duplicate
   exact path ownership, states outside the allowed vocabulary, and missing
   baseline inputs. The validator and its tests run in normal CI without
   network access.
6. **Architecture relationship.** Architecture v2 carries a narrow
   cross-reference to the subordinate realization program. This decision
   does not promote Architecture v2 from draft, redefine its engines, add
   architectural authority, or modify constitutional text.
7. **No implementation authority.** This decision authorizes coordination
   semantics only. Implementation workstreams (`RT-01` through `3D-01`),
   migrations, architecture promotion, merge, release, and branch or
   ruleset configuration each require their own gate under POL-0001.

## Consequences

**Positive:** parallel contributors can self-locate from `main` alone; silent
contract replacement becomes a detectable validator failure plus a review
duty; the delivery arc (program §5) is inspectable and evidence-bound.

**Costs:** registry upkeep is a standing duty of every workstream PR, and the
validator only detects structural drift — semantic conflicts still require
human, context-complete review
([STD-0001](../playbook/STD-0001-context-complete-reviews.md)).

## Reopening conditions

Reopen this decision if the registry creates coordination cost without
preventing drift, blocks legitimate parallel work, conflicts with a
higher-layer instrument, creates ownership deadlocks, or cannot reconstruct
why a delivered capability was authorized and accepted.

## Authority and scope

This record is subordinate to the
[Constitution v1.0](../constitution/Constitution-v1.0.md) and creates no
authority the Constitution does not grant. The operative act, once given, is
the Principal's explicit ratification; until then this decision binds no one
and the program remains proposed.
