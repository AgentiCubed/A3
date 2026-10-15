"""Exports: JSON, CSV, and a Power BI-ready star-schema ZIP.

"Power BI-compatible" (assumption A14) means flat CSVs with stable surrogate keys
arranged as dimensions + facts that Power BI can ingest and relate — not a native
.pbix. Dimension and fact tables share UUID keys so PBI can model relationships.
"""

from __future__ import annotations

import csv
import io
import uuid
import zipfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.evaluation import Evaluation
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.services import analytics_service, task_service


def _csv(fieldnames: list[str], rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


async def _project_rows(session: AsyncSession, project_id: uuid.UUID) -> dict:
    tasks = await task_service.list_tasks(session, project_id)
    executions = list(
        (
            await session.execute(
                select(TaskExecution)
                .join(Task, TaskExecution.task_id == Task.id)
                .where(Task.project_id == project_id)
            )
        ).scalars()
    )
    evaluations = list(
        (
            await session.execute(
                select(Evaluation)
                .join(TaskExecution, Evaluation.task_execution_id == TaskExecution.id)
                .join(Task, TaskExecution.task_id == Task.id)
                .where(Task.project_id == project_id)
            )
        ).scalars()
    )
    return {"tasks": tasks, "executions": executions, "evaluations": evaluations}


def _task_row(t: Task) -> dict:
    return {
        "task_id": str(t.id),
        "title": t.title,
        "status": t.status.value,
        "kanban_column": t.kanban_column.value,
        "estimate_hours": t.estimate_hours,
        "priority": t.priority,
        "assigned_agent_id": str(t.assigned_agent_id) if t.assigned_agent_id else "",
        "milestone_id": str(t.milestone_id) if t.milestone_id else "",
    }


async def tasks_csv(session: AsyncSession, *, project_id: uuid.UUID) -> str:
    rows = [_task_row(t) for t in await task_service.list_tasks(session, project_id)]
    return _csv(
        [
            "task_id",
            "title",
            "status",
            "kanban_column",
            "estimate_hours",
            "priority",
            "assigned_agent_id",
            "milestone_id",
        ],
        rows,
    )


async def project_json(session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID) -> dict:
    data = await _project_rows(session, project_id)
    dashboard = await analytics_service.project_dashboard(
        session, org_id=org_id, project_id=project_id
    )
    return {
        "project_id": str(project_id),
        "tasks": [_task_row(t) for t in data["tasks"]],
        "executions": [
            {
                "execution_id": str(e.id),
                "task_id": str(e.task_id),
                "agent_id": str(e.agent_id) if e.agent_id else "",
                "attempt_number": e.attempt_number,
                "state": e.state.value,
                "tokens_used": e.tokens_used,
                "cost_estimate": e.cost_estimate,
            }
            for e in data["executions"]
        ],
        "evaluations": [
            {
                "evaluation_id": str(ev.id),
                "task_execution_id": str(ev.task_execution_id),
                "verdict": ev.verdict.value,
                "score": ev.score,
                "evaluator_kind": ev.evaluator_kind.value,
            }
            for ev in data["evaluations"]
        ],
        "metrics": dashboard["metrics"],
        "agent_metrics": dashboard["agent_metrics"],
        "risk_matrix": dashboard["risk_matrix"],
    }


async def powerbi_zip(session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID) -> bytes:
    """Return a ZIP of dimension + fact CSVs with stable keys for Power BI."""
    data = await _project_rows(session, project_id)
    agents = list(
        (await session.execute(select(Agent).where(Agent.organization_id == org_id))).scalars()
    )

    dim_project = _csv(["project_id"], [{"project_id": str(project_id)}])
    dim_agent = _csv(
        ["agent_id", "name", "kind", "provider"],
        [
            {
                "agent_id": str(a.id),
                "name": a.name,
                "kind": a.kind.value,
                "provider": a.provider or "",
            }
            for a in agents
        ],
    )
    dim_task = _csv(
        ["task_id", "project_id", "title", "status", "assigned_agent_id"],
        [{**_task_row(t), "project_id": str(project_id)} for t in data["tasks"]],
    )
    fact_execution = _csv(
        [
            "execution_id",
            "task_id",
            "agent_id",
            "attempt_number",
            "state",
            "tokens_used",
            "cost_estimate",
        ],
        [
            {
                "execution_id": str(e.id),
                "task_id": str(e.task_id),
                "agent_id": str(e.agent_id) if e.agent_id else "",
                "attempt_number": e.attempt_number,
                "state": e.state.value,
                "tokens_used": e.tokens_used,
                "cost_estimate": e.cost_estimate,
            }
            for e in data["executions"]
        ],
    )
    fact_evaluation = _csv(
        ["evaluation_id", "task_execution_id", "verdict", "score", "evaluator_kind"],
        [
            {
                "evaluation_id": str(ev.id),
                "task_execution_id": str(ev.task_execution_id),
                "verdict": ev.verdict.value,
                "score": ev.score,
                "evaluator_kind": ev.evaluator_kind.value,
            }
            for ev in data["evaluations"]
        ],
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("dim_project.csv", dim_project)
        zf.writestr("dim_agent.csv", dim_agent)
        zf.writestr("dim_task.csv", dim_task)
        zf.writestr("fact_execution.csv", fact_execution)
        zf.writestr("fact_evaluation.csv", fact_evaluation)
        zf.writestr(
            "README.txt",
            "AgentiCubed Power BI export. Relate facts to dims on the shared *_id keys.\n",
        )
    return buf.getvalue()
