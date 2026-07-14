# DR-0001: Ground AgentiCubed in product language

- **Status:** Draft
- **Date:** 2026-07-14

## Product

AgentiCubed turns a project goal into finished work by planning the job,
splitting it into dependent tasks, assigning agents with the right
capabilities, executing each task, and checking the results against explicit
criteria.

When work fails review, AgentiCubed does not stop at the first bad output. It
records the attempt, chooses a remediation action, reruns or escalates the
work, and keeps the loop moving until a human can approve a deliverable.

## Triggering context

Repository history shows why this product explanation needs to come first. PR
#1 was closed as superseded after PR #4 merged the stabilization path, Issue
#5 split the remaining ideas into separate decisions so they could be reviewed
on their own merits, and Issue #6 opened because the working method was spread
across chat history, PR comments, and remembered conventions. Those artifacts
point to the same failure mode: review is becoming a bottleneck and the
evidence trail for why a change happened is harder to reconstruct than the
product behavior AgentiCubed is supposed to support.

## Product Alignment Table

| Paragraph | Product outcome served | Keep/Cut |
|---|---|---|
| Product paragraph 1 | Explains how AgentiCubed turns a goal into planned, assigned, executed, and checked work | Keep |
| Product paragraph 2 | Explains the remediation loop that turns failed work into a human-approvable deliverable | Keep |
| Triggering-context paragraph | Connects PR #1, PR #4, Issue #5, and Issue #6 to the review bottleneck and evidence trail behind this record | Keep |
| Any sentence that only describes abstract operating rules without tying them to planning, execution, review, or remediation in AgentiCubed | No product outcome served | Cut |
