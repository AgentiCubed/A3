# ADR-0004: Mandatory executor / evaluator separation

- **Status:** Accepted
- **Date:** 2026-06-25

## Context
A core integrity requirement is "separate executor and evaluator
responsibilities." If the agent that produces an output can also grade it, the
closed-loop remediation signal is corruptible (reward hacking, self-approval).

## Decision
For any `TaskExecution`, the evaluator is never the executing agent:
- Dispatch resolves the evaluator from a different registry slot
  (`default_role in {evaluator, either}` and `agent_id != executor_id`).
- Writing an `Evaluation` re-validates `evaluator_agent_id != execution.agent_id`
  and rejects a violation at the service layer.
- Deterministic validators and human approvals are always permitted evaluators.

## Consequences
- Evaluation signal is trustworthy enough to drive remediation.
- A project must have at least one eligible evaluator (agent, deterministic
  rubric, or human) per task type; matching surfaces this as a `BLOCKED` reason
  if none exists.
- Slight extra configuration burden, accepted as the cost of integrity.
