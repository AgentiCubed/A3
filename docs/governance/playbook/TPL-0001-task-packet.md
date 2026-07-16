# TPL-0001 — Task Packet Template

**Type:** Template  
**Version:** 1.0  
**Authority:** [POL-0001 Gate Workflow](POL-0001-gate-workflow.md), [STD-0001 Context-Complete Reviews](STD-0001-context-complete-reviews.md)  
**Status:** Active

---

## Purpose

This template defines the minimum structure for any task or review assignment in AgentiCubed. Every gate specification, task assignment, and review request shall include all fields marked **required**.

A packet that omits required fields is incomplete and shall not be acted upon until the missing fields are provided (see [STD-0001](STD-0001-context-complete-reviews.md), Failure Handling).

---

## Template

Copy and fill in the following for each task or review assignment:

---

```markdown
## Task / Review Packet

**ID:** <issue number, PR number, or locally unique identifier>  
**Date:** <YYYY-MM-DD>  
**Assigned to:** <executor or reviewer name/handle>  
**Authorized by:** <principal name — the human authorizing this gate>

---

### Objective [required]

<One or two sentences stating precisely what this task must accomplish. State the
end condition, not the process.>

---

### Scope [required]

**In scope:**
- <explicit list of what the executor/reviewer is authorized to change or assess>

**Out of scope (explicitly excluded):**
- <explicit list of what must not be changed or assessed in this gate>

---

### Acceptance conditions [required]

<The observable, verifiable criteria that must be satisfied for this gate to be
considered complete. Each condition should be independently checkable.>

- [ ] <condition 1>
- [ ] <condition 2>
- [ ] <condition 3>

---

### Authorization boundary [required]

<The limit beyond which the executor may not act without returning for explicit
authorization. State what is permitted and what requires a new gate.>

---

### Artifacts under review or modification [required for reviews]

<Exact repository path(s) and commit SHA, or PR number. Not "the latest draft."
Example: `docs/governance/constitution/Constitution-v1.0.md` at commit `e31c444`>

---

### Governing criteria [required for reviews]

<The specific standards, constitutional articles, policy sections, or ADRs against
which the artifact is being evaluated.>

---

### Expected deliverables [required]

<What the executor/reviewer must return when the gate is complete.>

- <deliverable 1 — e.g., PR with changes, evidence summary, review findings>
- <deliverable 2>

---

### Stop conditions [required]

<Conditions under which the executor/reviewer shall halt rather than continue,
and return the gap to the principal.>

- Halt if: <condition requiring escalation>
- Halt if: <condition requiring escalation>

---

### Non-goals [recommended]

<Optional but recommended. Explicit statement of what this gate is not trying to
accomplish, to prevent scope drift.>

---

### Context and constraints [as needed]

<Background, related issues, governing instruments, known constraints, or
dependencies the executor/reviewer needs to complete the work. This section must
be complete enough that no prior conversational context is needed.>

```

---

## Notes on Use

**Be specific about acceptance conditions.** "Looks good" is not a condition. "All 102 backend tests pass with `make check` green" is a condition.

**Be explicit about exclusions.** If you do not want the executor to modify tests, say so. Silence is not restriction.

**Include exact artifact references for reviews.** A review of "the current version" is not reproducible. A review of `docs/governance/constitution/Constitution-v1.0.md` at commit `e31c444` is.

**Stop conditions protect both parties.** Defining when to halt prevents the executor from overstepping and gives the principal a clear signal to look for. Omitting stop conditions places the burden of scope judgment on the executor alone.
