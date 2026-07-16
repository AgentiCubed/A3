# IER-0001 — Evolution of the Constitutional Baseline

## Current Formulation

The current constitutional authority consists of Constitution v1.0 together with ratified Amendment A-0001. Constitution v1.0 remains the historical baseline; amendments are preserved separately with stable citations, ratification records, and release evidence.

## Stage 1 — Governance as Ad Hoc Prompting

Initial formulation:

> Model prompts and human approvals could carry the engineering discipline developed during stabilization.

Assumptions:

- conversational instructions would remain available and consistent;
- capable models would infer the same governance rules;
- repository state could be reconstructed from recent memory.

Failure:

The rules expanded faster than they could be remembered or applied consistently. Different models used different terminology and lacked a shared precedence structure.

## Stage 2 — A Small Constitution

Revised formulation:

> A short Constitution should govern enduring authority, evidence, delegation, bounded autonomy, stopping, precedence, supremacy, and amendment.

Trigger:

Cross-model review exposed missing sovereignty, amendment, rights, precedence, non-convergence, and emergency doctrines.

Discarded branch:

A comprehensive governance framework containing implementation detail, feature lists, repository structure, thresholds, and procedures.

Reason discarded:

Fast-changing implementation content would make the Constitution brittle and produce governance for its own sake.

## Stage 3 — Constitution v1.0 as a Single Frozen Text

Revised formulation:

> After adversarial and mechanical review, the exact v1.0 text should be frozen and tagged as the baseline.

Assumptions:

- the final audit had eliminated all contradictions;
- companion documents could be created after ratification without reopening the text;
- publication could proceed directly from the ratified document.

Contradiction discovered:

Article VII required a Halt for insufficient or ambiguous authority while Article IX described its own listed Executor/Evaluator Halt grounds as exhaustive. The relationship was inferable but not explicit.

Operational failures also showed that the baseline files had been committed directly to `main`, and companion documents were not fully aligned.

## Stage 4 — Corrective Amendment Rather Than Silent Rewrite

Revised formulation:

> Preserve Constitution v1.0 and correct the ambiguity through Amendment A-0001 under Article XII.

Evidence causing revision:

- the Constitution already described itself as ratified;
- RR-0001 established v1.0 as the baseline;
- Article XII required historical continuity;
- silently editing v1.0 would erase the evidence of the defect and bypass the amendment process.

Discarded branches:

1. Edit Constitution-v1.0.md directly.
2. Pretend the ambiguity was only Commentary.
3. Revert the direct-to-main commits and manufacture a retroactive clean history.

Why rejected:

Each option would reduce historical truth or create unnecessary repository churn.

## Stage 5 — Constitutional Authority as a Versioned Set

Current decision:

> The baseline is not only one mutable file. It is a durable set: original Constitution, ratified amendments, ratification history, subordinate procedure, verified merge commit, tag, and release.

Accepted by:

James Richmond as Principal, through explicit ratification, merge, tag, and release authorization.

Evidence:

- PR #7
- merge commit `e31c44460f2d6416cb2c2b4398c6b3a658147f29`
- successful main CI run #12
- release `constitution-v1.0-a0001`

## General Learning

The most valuable evolution was not from weaker wording to stronger wording. It was from treating governance as a polished document to treating it as an evidence-backed state transition system with preserved history.

## Reopening Conditions

Reconsider this formulation if:

- amendments become numerous enough that separate documents impair discoverability;
- tooling cannot reliably resolve the effective constitutional text;
- a future amendment changes the versioning model;
- the distinction between historical baseline and effective authority causes repeated implementation errors;
- evidence shows a consolidated restatement can preserve stable citations and historical continuity better than separate amendments.

## Linked Records

- [FR-0001](./FR-0001-constitutional-release-process.md)
- [RM-0001](./RM-0001-constitutional-release-process.md)
- [RL-0001](./RL-0001-failure-first-memory.md)
- Constitution v1.0
- Amendment A-0001
- RR-0001
- DR-0001
- PR #7
- Release `constitution-v1.0-a0001`