"""Output evaluation: deterministic rubric + optional evaluator agent.

Executor/evaluator separation is enforced here (security-model §6, ADR-0004):
an evaluator agent may never be the agent that produced the execution. Every
Evaluation and its criteria are immutable.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import EvaluatorKind
from app.core.roles import ActorType
from app.evaluation.rubric import evaluate_deterministic
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationCriterion
from app.models.task_execution import TaskExecution
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import AgentRunRequest


class EvaluatorConflict(Exception):
    """The evaluator agent is the same as the executor agent."""


def _review_prompt(output: str, specs: list[dict]) -> str:
    criteria = (
        ", ".join(s.get("key", s.get("check", "criterion")) for s in specs) or "general quality"
    )
    return (
        "You are an independent evaluator. Review the following output against "
        f"these criteria: {criteria}.\n\n--- OUTPUT ---\n{output}\n--- END ---\n"
        "Give a brief critique and note any gaps."
    )


async def evaluate_execution(
    session: AsyncSession,
    *,
    execution: TaskExecution,
    rubric_specs: list[dict],
    evaluator_agent: Agent | None,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
) -> Evaluation:
    """Evaluate one execution's output. Returns the immutable Evaluation row."""
    outcome = evaluate_deterministic(execution.output or "", rubric_specs)

    evaluator_kind = EvaluatorKind.DETERMINISTIC
    evaluator_agent_id: uuid.UUID | None = None
    summary = f"Deterministic rubric: {outcome.verdict.value} (score={outcome.score:.2f})"

    if evaluator_agent is not None:
        if evaluator_agent.id == execution.agent_id:
            raise EvaluatorConflict()  # executor must not grade itself
        evaluator_kind = EvaluatorKind.AGENT
        evaluator_agent_id = evaluator_agent.id
        adapter = get_adapter(evaluator_agent.provider)
        cred = (evaluator_agent.config or {}).get("api_key_ref")
        try:
            result = await adapter.run(
                AgentRunRequest(
                    prompt=_review_prompt(execution.output or "", rubric_specs),
                    model=evaluator_agent.model,
                    credential_ref=cred,
                )
            )
            summary = f"Evaluator '{evaluator_agent.name}': {result.output}"
        except (
            Exception
        ) as exc:  # noqa: BLE001 - evaluator failure falls back to the deterministic gate
            summary = f"evaluator agent error ({type(exc).__name__}); deterministic gate used"

    evaluation = Evaluation(
        organization_id=execution.organization_id,
        task_execution_id=execution.id,
        evaluator_agent_id=evaluator_agent_id,
        evaluator_kind=evaluator_kind,
        verdict=outcome.verdict,
        score=outcome.score,
        summary=summary,
        gaps=outcome.gaps,
    )
    session.add(evaluation)
    await session.flush()

    for cr in outcome.criteria:
        session.add(
            EvaluationCriterion(
                organization_id=execution.organization_id,
                evaluation_id=evaluation.id,
                criterion=cr.key,
                weight=cr.weight,
                passed=cr.passed,
                score=cr.score,
                notes=cr.notes or None,
            )
        )

    await record_audit(
        session,
        organization_id=execution.organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="evaluation.recorded",
        entity_type="Evaluation",
        entity_id=evaluation.id,
        after={
            "verdict": outcome.verdict.value,
            "score": outcome.score,
            "kind": evaluator_kind.value,
        },
    )
    return evaluation


async def list_evaluations_for_task(
    session: AsyncSession, *, org_id: uuid.UUID, task_id: uuid.UUID
) -> list[Evaluation]:
    stmt = (
        select(Evaluation)
        .join(TaskExecution, Evaluation.task_execution_id == TaskExecution.id)
        .where(Evaluation.organization_id == org_id, TaskExecution.task_id == task_id)
        .order_by(Evaluation.created_at)
    )
    return list((await session.execute(stmt)).scalars().all())
