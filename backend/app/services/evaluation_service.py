"""Output evaluation: deterministic rubric + optional evaluator agent.

Executor/evaluator separation is enforced here (security-model §6, ADR-0004):
an evaluator agent may never be the agent that produced the execution. Every
Evaluation and its criteria are immutable.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import EvaluatorKind, Verdict
from app.core.roles import ActorType
from app.evaluation.rubric import evaluate_deterministic
from app.evaluation.specs import normalize_rubric_specs, rubric_sha256
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationCriterion
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.adapters.registry import get_adapter
from app.orchestration.ports import AgentRunRequest
from app.services import acceptance_boundary_service


class EvaluatorConflict(Exception):
    """The evaluator agent is the same as the executor agent."""


# Verdict ordering: lower = worse. Combining takes the WORSE of the two signals,
# so an evaluator agent can downgrade a deterministic PASS but can never upgrade a
# hard deterministic FAIL (issue 0004 / security-model §6).
_VERDICT_ORDER = {Verdict.FAIL: 0, Verdict.NEEDS_REVISION: 1, Verdict.PASS: 2}


def combine_verdicts(deterministic: Verdict, agent: Verdict) -> Verdict:
    """Return the stricter (worse) of the deterministic and agent verdicts."""
    return deterministic if _VERDICT_ORDER[deterministic] <= _VERDICT_ORDER[agent] else agent


# The structured contract the evaluator agent must answer with (WS-4 / issue
# 0004). Adapters that support native structured output can enforce it; for the
# rest the prompt instructs it and ``parse_evaluator_verdict`` fails closed.
VERDICT_CONTRACT = "verdict_json_v1"

_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class AgentVerdict:
    """Parsed evaluator-agent response. ``malformed`` means we failed closed."""

    verdict: Verdict
    score: float | None
    critique: str
    gaps: list[str] = field(default_factory=list)
    malformed: bool = False


def _fail_closed(reason: str) -> AgentVerdict:
    return AgentVerdict(
        verdict=Verdict.NEEDS_REVISION,
        score=None,
        critique=f"evaluator response rejected ({reason}); failing closed",
        malformed=True,
    )


def parse_evaluator_verdict(raw: str) -> AgentVerdict:
    """Fail-closed parser for the evaluator's JSON verdict contract.

    Accepts a bare JSON object, optionally wrapped in a ``` fence. Anything
    else — prose, wrong types, unknown verdict, out-of-range score — yields
    NEEDS_REVISION with ``malformed=True``. A broken or lying judge can force
    human review, but it can never silently PASS work (security-model §6).
    """
    text = (raw or "").strip()
    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return _fail_closed("not valid JSON")
    if not isinstance(data, dict):
        return _fail_closed("not a JSON object")
    try:
        verdict = Verdict(data.get("verdict"))
    except ValueError:
        return _fail_closed("unknown verdict value")
    score = data.get("score")
    if score is not None:
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
            return _fail_closed("score out of range")
        score = float(score)
    critique = data.get("critique")
    if critique is not None and not isinstance(critique, str):
        return _fail_closed("critique not a string")
    gaps = data.get("gaps")
    if gaps is None:
        gaps = []
    if not isinstance(gaps, list) or any(not isinstance(g, str) for g in gaps):
        return _fail_closed("gaps not a list of strings")
    return AgentVerdict(verdict=verdict, score=score, critique=critique or "", gaps=gaps)


def _review_prompt(output: str, specs: list[dict]) -> str:
    criteria = (
        ", ".join(s.get("key", s.get("check", "criterion")) for s in specs) or "general quality"
    )
    return (
        "You are an independent evaluator. Review the following output against "
        f"these criteria: {criteria}.\n\n--- OUTPUT ---\n{output}\n--- END ---\n"
        "Respond with ONLY a JSON object of the form "
        '{"verdict": "pass" | "needs_revision" | "fail", "score": <number 0..1>, '
        '"critique": "<short critique>", "gaps": ["<gap>", ...]}. '
        "No text outside the JSON object."
    )


async def evaluate_execution(
    session: AsyncSession,
    *,
    execution: TaskExecution,
    rubric_specs: list[dict],
    evaluator_agent: Agent | None,
    rubric_source: str,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
) -> Evaluation:
    """Evaluate one execution's output. Returns the immutable Evaluation row."""
    normalized_specs = normalize_rubric_specs(rubric_specs)
    rubric_digest = rubric_sha256(normalized_specs)
    outcome = evaluate_deterministic(execution.output or "", normalized_specs)

    evaluator_kind = EvaluatorKind.DETERMINISTIC
    evaluator_agent_id: uuid.UUID | None = None
    final_verdict = outcome.verdict
    summary = f"Deterministic rubric: {outcome.verdict.value} (score={outcome.score:.2f})"

    agent_gaps: list[str] = []
    agent_malformed: bool | None = None
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
                    prompt=_review_prompt(execution.output or "", normalized_specs),
                    model=evaluator_agent.model,
                    credential_ref=cred,
                    params={"expected_format": VERDICT_CONTRACT},
                )
            )
            agent_verdict = parse_evaluator_verdict(result.output)
        except Exception as exc:  # noqa: BLE001 - an unreachable judge fails closed
            agent_verdict = _fail_closed(f"evaluator agent error: {type(exc).__name__}")
        agent_gaps = agent_verdict.gaps
        agent_malformed = agent_verdict.malformed
        malformed_note = " [failed closed]" if agent_verdict.malformed else ""
        final_verdict = combine_verdicts(outcome.verdict, agent_verdict.verdict)
        summary = (
            f"Evaluator '{evaluator_agent.name}' verdict={agent_verdict.verdict.value}"
            f"{malformed_note}; deterministic={outcome.verdict.value}; "
            f"combined={final_verdict.value}. {agent_verdict.critique}"
        )

    combined_gaps = list(outcome.gaps or []) + agent_gaps
    project_scope = (
        await session.execute(
            select(Task.project_id, Task.organization_id)
            .join(TaskExecution, TaskExecution.task_id == Task.id)
            .where(TaskExecution.id == execution.id)
        )
    ).one_or_none()
    if project_scope is None:
        raise acceptance_boundary_service.ProjectNotFound()
    project_id, project_org_id = project_scope
    await acceptance_boundary_service.claim_acceptance_write(
        session,
        project_id=project_id,
        org_id=project_org_id,
    )
    evaluation = Evaluation(
        organization_id=execution.organization_id,
        task_execution_id=execution.id,
        evaluator_agent_id=evaluator_agent_id,
        evaluator_kind=evaluator_kind,
        verdict=final_verdict,
        score=outcome.score,
        summary=summary,
        gaps=combined_gaps or None,
        rubric_specs=normalized_specs,
        rubric_sha256=rubric_digest,
        rubric_source=rubric_source,
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
            "verdict": final_verdict.value,
            "score": outcome.score,
            "kind": evaluator_kind.value,
            "rubric_sha256": rubric_digest,
            "rubric_source": rubric_source,
            # None for deterministic-only evaluations; True means the agent's
            # response violated the contract and the verdict failed closed.
            "agent_malformed": agent_malformed,
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
