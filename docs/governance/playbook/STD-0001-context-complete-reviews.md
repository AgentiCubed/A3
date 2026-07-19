# STD-0001 — Context-Complete Reviews

**Type:** Standard  
**Version:** 1.0  
**Authority:** Article VI (Evidence and Verification) of the [Constitution v1.0](../constitution/Constitution-v1.0.md); [POL-0001 Gate Workflow](POL-0001-gate-workflow.md)  
**Source:** Issue #6, comment 2026-07-14 (context-complete reviews governance rule)  
**Status:** Active

---

## Purpose

This Standard establishes the minimum requirements for any review or task assignment performed in AgentiCubed. A review assignment must contain all context needed to complete the review without relying on conversational memory, prior sessions, or information not present in the assignment itself.

---

## Rule

**Reviews must be context-complete.**

A reviewer — human or autonomous — shall require no external conversational memory or prior session context to perform the assigned review.

---

## Minimum Review Packet

Every review assignment shall include:

| Field | Description |
|---|---|
| **Artifact** | The complete artifact under review, or an exact, immutable reference (repository path + commit SHA) |
| **Review objective** | What the reviewer is asked to assess |
| **Scope** | What is in scope and what is explicitly excluded |
| **Non-goals** | What the review is not being asked to change, assess, or decide |
| **Constraints** | Applicable constitutional, policy, or technical constraints governing the work |
| **Governing criteria** | The specific standards or conditions the artifact must satisfy |
| **Expected deliverables** | What the reviewer must return |
| **Success conditions** | Observable criteria indicating the review is complete and satisfactory |
| **Stop conditions** | Conditions under which the reviewer must stop rather than continue |
| **Authorization boundary** | The current limit of the reviewer's authority |

---

## Insufficient Assignments

The following forms of assignment are insufficient on their own:

- "Review the latest draft" — without an exact repository path and commit SHA
- "Check this" — without a review objective and governing criteria
- "Does this look right?" — without acceptance conditions
- Any assignment that requires the reviewer to recall prior conversational context to understand what is being asked

---

## Failure Handling

When required context is missing, the reviewer shall:

1. Stop.
2. Identify specifically what is missing (missing artifact reference, missing criteria, etc.).
3. Return the gap to the assigning Principal.
4. Not fabricate quotations, defects, conclusions, or missing context.

Proceeding with an incomplete assignment and producing speculative conclusions is a worse outcome than stopping and requesting the missing information.

---

## Application

This standard applies to:

- all review assignments given to autonomous agents;
- all review assignments given to human contributors;
- all gate specifications under [POL-0001](POL-0001-gate-workflow.md);
- all task packets under [TPL-0001](TPL-0001-task-packet.md).

The standard is satisfied when a reviewer with no prior knowledge of the project could perform the assigned review using only the information provided.

---

## Rationale

Conversational context is incomplete, non-portable, and unavailable to future reviewers. A review that depends on remembered chat state:

- cannot be independently reproduced;
- cannot be audited;
- degrades over time as context fades;
- is unavailable to contributors who join later.

Context-complete assignments create reviews that remain valid across contributors, sessions, and time.
