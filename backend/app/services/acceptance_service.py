"""Acceptance-criteria gate (WS-4b): completion is earned, not declared.

A project's ``acceptance_criteria`` compile into deterministic checks, and the
close path refuses to mark the project CLOSED while any check fails — unless a
human explicitly acknowledges the unmet criteria (deliberate abandonment),
which is recorded. Either way, a project can never be *silently* completed
with its acceptance criteria unsatisfied.

Supported ``acceptance_criteria`` shapes (both keys may be combined):

- ``{"criteria": [<rubric spec>, ...]}`` — rubric specs (same shape the task
  rubric engine uses: ``{"key", "check", "params", "weight"}``) evaluated
  against the corpus of the project's successful execution outputs. Unknown
  checks fail closed (rubric engine behavior).
- ``{"deliverables": ["brief", ...]}`` — each name must match a stored
  project artifact (case-insensitive substring, ignoring spaces/hyphens/
  underscores, so "demand chart" matches "widget-demand-chart.png").

An empty or absent ``acceptance_criteria`` defines no gate (nothing to hold
the project to), which the report makes explicit via ``evaluated=False``.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Verdict
from app.evaluation.rubric import evaluate_deterministic
from app.models.artifact import Artifact
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.state_machine.states import ExecutionState


@dataclass(frozen=True)
class CriterionStatus:
    key: str
    kind: str  # "rubric" | "deliverable"
    passed: bool
    notes: str

    def to_dict(self) -> dict:
        return {"key": self.key, "kind": self.kind, "passed": self.passed, "notes": self.notes}


@dataclass(frozen=True)
class AcceptanceReport:
    evaluated: bool  # False when the project defines no acceptance criteria
    satisfied: bool  # True when every evaluated criterion passed (or none exist)
    results: list[CriterionStatus]

    @property
    def unmet(self) -> list[CriterionStatus]:
        return [r for r in self.results if not r.passed]

    def to_dict(self) -> dict:
        return {
            "evaluated": self.evaluated,
            "satisfied": self.satisfied,
            "results": [r.to_dict() for r in self.results],
        }


def _normalize(name: str) -> str:
    """Case/separator-insensitive form for deliverable-name matching."""
    return re.sub(r"[\s_\-]+", "", name.lower())


async def _output_corpus(session: AsyncSession, project_id: uuid.UUID) -> str:
    """Accepted execution outputs of the project's tasks, newest last.

    Executions without an evaluation are successful by execution state alone.
    Once evaluated, only a PASS may contribute to project acceptance; rejected
    attempts must never help a project earn completion.
    """
    stmt = (
        select(TaskExecution.output)
        .join(Task, TaskExecution.task_id == Task.id)
        .outerjoin(Evaluation, Evaluation.task_execution_id == TaskExecution.id)
        .where(
            Task.project_id == project_id,
            TaskExecution.state == ExecutionState.COMPLETED,
            or_(Evaluation.id.is_(None), Evaluation.verdict == Verdict.PASS),
        )
        .order_by(TaskExecution.finished_at)
    )
    outputs = [o for o in (await session.execute(stmt)).scalars().all() if o]
    return "\n\n".join(outputs)


async def evaluate_project_acceptance(
    session: AsyncSession, *, project: Project
) -> AcceptanceReport:
    """Evaluate the project's acceptance criteria against its actual record."""
    spec = project.acceptance_criteria or {}
    malformed = _malformed_spec_reason(spec)
    if malformed:
        return AcceptanceReport(
            evaluated=True,
            satisfied=False,
            results=[
                CriterionStatus(
                    key="acceptance_criteria", kind="rubric", passed=False, notes=malformed
                )
            ],
        )
    rubric_specs = spec.get("criteria") or []
    deliverables = spec.get("deliverables") or []
    if not rubric_specs and not deliverables:
        return AcceptanceReport(evaluated=False, satisfied=True, results=[])

    results: list[CriterionStatus] = []

    if rubric_specs:
        corpus = await _output_corpus(session, project.id)
        outcome = evaluate_deterministic(corpus, list(rubric_specs))
        for cr in outcome.criteria:
            results.append(
                CriterionStatus(key=cr.key, kind="rubric", passed=cr.passed, notes=cr.notes)
            )

    if deliverables:
        artifact_names = [
            _normalize(n)
            for n in (
                await session.execute(
                    select(Artifact.name).where(Artifact.project_id == project.id)
                )
            )
            .scalars()
            .all()
        ]
        for wanted in deliverables:
            found = any(_normalize(str(wanted)) in name for name in artifact_names)
            results.append(
                CriterionStatus(
                    key=str(wanted),
                    kind="deliverable",
                    passed=found,
                    notes="" if found else f"no stored artifact matches '{wanted}'",
                )
            )

    return AcceptanceReport(
        evaluated=True, satisfied=all(r.passed for r in results), results=results
    )


def _malformed_spec_reason(spec: object) -> str | None:
    """Return a fail-closed diagnostic for unsupported persisted specifications."""
    if not isinstance(spec, dict):
        return "acceptance criteria must be an object"
    unknown = set(spec) - {"criteria", "deliverables"}
    if unknown:
        return f"unsupported acceptance criteria keys: {', '.join(sorted(unknown))}"
    criteria = spec.get("criteria", [])
    deliverables = spec.get("deliverables", [])
    if criteria is not None and (
        not isinstance(criteria, list) or any(not isinstance(item, dict) for item in criteria)
    ):
        return "criteria must be a list of rubric objects"
    if deliverables is not None and (
        not isinstance(deliverables, list)
        or any(not isinstance(item, str) or not item.strip() for item in deliverables)
    ):
        return "deliverables must be a list of non-empty strings"
    return None
