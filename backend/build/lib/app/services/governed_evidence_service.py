"""Shared proof that governed work passed its approved evaluation policy."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import EvaluatorKind, Verdict
from app.evaluation.specs import normalize_rubric_specs, rubric_sha256
from app.models.evaluation import Evaluation
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.state_machine.states import ExecutionState


class EvidenceInvalid(Exception):
    """One or more governed tasks lack exact passing evidence."""

    def __init__(self, tasks: list[dict]):
        self.tasks = tasks
        super().__init__("approved plan task evidence is missing or invalid")


async def passing_evaluation_ids(
    session: AsyncSession,
    tasks: list[Task],
) -> dict[str, str]:
    """Return exact passing evaluation ids or fail closed with diagnostics."""
    evaluation_ids: dict[str, str] = {}
    invalid: list[dict] = []
    for task in tasks:
        execution = await session.scalar(
            select(TaskExecution)
            .where(
                TaskExecution.task_id == task.id,
                TaskExecution.state == ExecutionState.COMPLETED,
            )
            .order_by(TaskExecution.finished_at.desc(), TaskExecution.id.desc())
            .limit(1)
        )
        if execution is None:
            invalid.append(
                {
                    "task_key": task.source_plan_task_key,
                    "task_id": str(task.id),
                    "reason": "successful_execution_missing",
                }
            )
            continue
        evaluation = await session.scalar(
            select(Evaluation)
            .where(Evaluation.task_execution_id == execution.id)
            .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
            .limit(1)
        )
        specs = normalize_rubric_specs(task.acceptance_criteria)
        context = execution.input_context if isinstance(execution.input_context, dict) else {}
        context_policy = context.get("evaluation")
        raw_sources = context_policy.get("sources") if isinstance(context_policy, dict) else None
        context_sources = raw_sources if isinstance(raw_sources, list) else []
        expected_evaluator_id = (
            str(task.evaluator_agent_id) if task.evaluator_agent_id is not None else None
        )
        recorded_evaluator_id = (
            context_policy.get("evaluator_agent_id") if isinstance(context_policy, dict) else None
        )
        recorded_max_remediations = (
            context_policy.get("max_remediations") if isinstance(context_policy, dict) else None
        )
        try:
            evaluated_specs = normalize_rubric_specs(
                evaluation.rubric_specs if evaluation is not None else None
            )
            context_specs = normalize_rubric_specs(
                context_policy.get("rubric_specs") if isinstance(context_policy, dict) else None
            )
        except ValueError:
            evaluated_specs = []
            context_specs = []
        effective_hash = rubric_sha256(evaluated_specs)
        allowed_sources = context_sources in (["persisted"], ["persisted", "request"])
        evaluator_matches_context = (
            evaluation is not None
            and (
                str(evaluation.evaluator_agent_id)
                if evaluation.evaluator_agent_id is not None
                else None
            )
            == recorded_evaluator_id
        )
        approved_evaluator_enforced = (
            expected_evaluator_id is None or recorded_evaluator_id == expected_evaluator_id
        )
        evaluator_kind_matches = evaluation is not None and (
            (
                recorded_evaluator_id is None
                and evaluation.evaluator_kind == EvaluatorKind.DETERMINISTIC
            )
            or (
                recorded_evaluator_id is not None
                and evaluation.evaluator_kind == EvaluatorKind.AGENT
            )
        )
        remediation_cap_valid = (
            isinstance(recorded_max_remediations, int)
            and not isinstance(recorded_max_remediations, bool)
            and 0 <= recorded_max_remediations <= task.max_remediations
        )
        valid = (
            evaluation is not None
            and execution.organization_id == task.organization_id
            and execution.agent_id == task.assigned_agent_id
            and evaluation.organization_id == task.organization_id
            and evaluation.verdict == Verdict.PASS
            and evaluated_specs[: len(specs)] == specs
            and evaluation.rubric_sha256 == effective_hash
            and isinstance(context_policy, dict)
            and context_specs == evaluated_specs
            and context_policy.get("rubric_sha256") == effective_hash
            and allowed_sources
            and evaluation.rubric_source == "+".join(context_sources)
            and evaluator_matches_context
            and approved_evaluator_enforced
            and evaluator_kind_matches
            and remediation_cap_valid
        )
        if not valid:
            invalid.append(
                {
                    "task_key": task.source_plan_task_key,
                    "task_id": str(task.id),
                    "reason": "passing_approved_evaluation_missing",
                }
            )
            continue
        evaluation_ids[str(task.source_plan_task_key)] = str(evaluation.id)
    if invalid:
        raise EvidenceInvalid(invalid)
    return evaluation_ids
