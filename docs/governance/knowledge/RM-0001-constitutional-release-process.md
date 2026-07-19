# RM-0001 — Why the Constitutional Release Required Repeated Recovery

## Linked Failure

[FR-0001 — Constitutional Release Process Failures](./FR-0001-constitutional-release-process.md)

## Question

Why did a documentation-only release require repeated correction despite strong governance principles and multiple capable reviewers?

## Verified Facts

- Repository state was sometimes inferred from conversation instead of read from GitHub.
- GitHub's web interface exposed branch, commit, file, PR, check, tag, and release contexts through different screens with overlapping visual language.
- The user needed short, single-action instructions for unfamiliar GitHub operations.
- Reviewers without authenticated repository access received references rather than complete file contents.
- Ratification, amendment, tag, and release were treated as related but occasionally collapsed into one conceptual event.
- The process ultimately succeeded after evidence gates were reintroduced.

## Hypotheses

### H1 — The primary failure was tool unfamiliarity

Confidence: medium.

GitHub's web editing, branch selector, commit snapshots, PR metadata editor, merge methods, Actions numbering, and Release UI each introduced local confusion.

Counter-evidence: tool familiarity alone would not explain premature completion claims or context-incomplete reviewer packets.

### H2 — The primary failure was state compression in conversation

Confidence: high.

Long conversational context compressed proposed state, intended state, and verified Git state into a single narrative. Once a sentence said a file or branch existed, later reasoning sometimes treated it as fact.

Counter-evidence: direct connector access later restored accuracy quickly, so the problem was not memory alone; it was failure to privilege repository evidence consistently.

### H3 — The governance model was too elaborate for the task

Confidence: low to medium.

The number of gates increased interactions and exposed more opportunities for error.

Counter-evidence: the gates detected a real constitutional contradiction, incomplete DR procedure, inconsistent RR status, truncated PR metadata, prohibited merge method, and unverified main state. Removing the gates would have hidden rather than prevented those defects.

### H4 — Authority stages were defined, but artifact-state semantics were not

Confidence: high.

The process distinguished edit, commit, PR, merge, tag, and release authority. It did not initially define the status transitions of the Constitution, Amendment, Ratification Record, tag, and release with equal precision. This allowed `proposed`, `ratified`, `effective`, `merged`, `tagged`, and `published` to drift.

## Rejected Explanations

### Individual incompetence

Rejected. The failure pattern crossed human, model, UI, and connector boundaries. It is better explained by state ambiguity, incomplete handoffs, and missing operational templates.

### More reviewers would have prevented the failures

Rejected. Review quantity did not help when reviewers lacked the exact artifacts or repository access. Context completeness and independent evidence mattered more than headcount.

### The errors were harmless because the work was documentation-only

Rejected. Governance text changes authority claims. A contradictory or incorrectly tagged document can misdirect future repository and product actions even without changing runtime code.

## Human and System Factors

- **Interface opacity:** GitHub's context selector can represent a branch or detached commit.
- **Cognitive load:** long sequences mixed drafting, Git operations, constitutional interpretation, and UI tutoring.
- **State-name collision:** PR #7 and workflow run #12 looked like competing identifiers.
- **Narrative momentum:** prior confident statements created pressure to continue rather than re-verify.
- **Artifact fragmentation:** canonical text lived temporarily in chat, uploaded files, GitHub tabs, and model outputs.
- **Authorization optimism:** broad permission encouraged forward motion but did not remove the need for evidence gates.

## Mental Model Update

Old model:

> A carefully designed governance process plus capable reviewers will reliably produce a clean release.

Updated model:

> Governance quality depends on explicit artifact states, context-complete packets, repository evidence at every transition, and interfaces that make the current state visible. Principles constrain behavior; they do not substitute for state verification.

## Generalized Principles

1. **Git state outranks narrative state.** A claim about files, branches, commits, checks, tags, or releases is provisional until retrieved from the repository.
2. **Review quality is bounded by packet completeness.** A brilliant reviewer with partial context produces less reliable output than an ordinary reviewer with the exact artifact and criteria.
3. **Status words require a state machine.** Proposed, ratified, effective, merged, tagged, and published must each have explicit entry evidence.
4. **Failure documentation must preserve cognition.** Facts explain what happened; rumination preserves why capable actors believed the wrong thing.
5. **Friction is diagnostic.** Repeated requests for micro-steps indicate a procedure or interface that should be documented or automated.

## Future Heuristics

- Begin every repository session with repo, branch/ref, HEAD, and status evidence.
- Put exact source text inside every external review packet.
- Use one canonical artifact location before drafting begins.
- Maintain a release-state checklist with evidence fields.
- Never label an amendment `Ratified` until RR, effective text, and authority decision agree.
- Never create a tag from a branch name when the intended commit SHA is known.
- Treat connector or UI failure as a stop, not an invitation to narrate success.
- Record each failure while evidence is fresh; write rumination only after containment.

## Remaining Uncertainty

- Whether the best maintainer path is a visual GitHub guide, a CLI procedure, or a future automated release assistant.
- How much process should be mandatory for low-risk documentation changes.
- Whether confidence scores improve reasoning quality or create false precision.
- How future agents should detect that an existing record has become stale.