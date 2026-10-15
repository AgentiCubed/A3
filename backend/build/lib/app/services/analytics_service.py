"""Analytics service: load project data, compute metrics, materialize snapshots."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.compute import (
    AgentExecRow,
    agent_metrics,
    project_metrics,
    risk_matrix,
)
from app.core.enums import ApprovalStatus, RiskStatus
from app.models.agent import Agent
from app.models.approval import Approval
from app.models.evaluation import Evaluation
from app.models.metric import AgentMetric, ProjectMetric
from app.models.risk import Risk
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.services import task_service


async def _load(session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID) -> dict:
    tasks = await task_service.list_tasks(session, project_id)
    agents = {
        a.id: a.name
        for a in (
            await session.execute(select(Agent).where(Agent.organization_id == org_id))
        ).scalars()
    }
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
    risks = list(
        (
            await session.execute(
                select(Risk).where(Risk.project_id == project_id, Risk.status != RiskStatus.CLOSED)
            )
        ).scalars()
    )
    pending = len(
        list(
            (
                await session.execute(
                    select(Approval).where(
                        Approval.project_id == project_id,
                        Approval.status == ApprovalStatus.PENDING,
                    )
                )
            ).scalars()
        )
    )
    return {
        "tasks": tasks,
        "agents": agents,
        "executions": executions,
        "evaluations": evaluations,
        "risks": risks,
        "pending_approvals": pending,
    }


async def project_dashboard(
    session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID
) -> dict:
    data = await _load(session, org_id, project_id)
    tasks = data["tasks"]
    executions = data["executions"]
    evaluations = data["evaluations"]
    risks = data["risks"]

    eval_by_exec = {e.task_execution_id: e for e in evaluations}

    pm = project_metrics(
        task_statuses=[t.status.value for t in tasks],
        execution_states=[e.state.value for e in executions],
        evaluation_verdicts=[e.verdict.value for e in evaluations],
        evaluation_scores=[e.score for e in evaluations],
        open_risk_severities=[r.severity for r in risks],
        pending_approvals=data["pending_approvals"],
    )

    rows: list[AgentExecRow] = []
    for ex in executions:
        if ex.agent_id is None:
            continue
        ev = eval_by_exec.get(ex.id)
        rows.append(
            AgentExecRow(
                agent_id=str(ex.agent_id),
                agent_name=data["agents"].get(ex.agent_id, "unknown"),
                state=ex.state.value,
                tokens=ex.tokens_used,
                cost=ex.cost_estimate,
                score=ev.score if ev else None,
                passed=(ev.verdict.value == "pass") if ev else None,
            )
        )
    am = agent_metrics(rows)
    rm = risk_matrix([(r.likelihood, r.impact) for r in risks])

    timeline = await task_service.compute_timeline(session, project_id)

    return {
        "metrics": pm.metrics,
        "status_breakdown": pm.status_breakdown,
        "agent_metrics": [
            {"agent_id": a.agent_id, "agent_name": a.agent_name, "metrics": a.metrics} for a in am
        ],
        "risk_matrix": rm,
        "timeline": {
            "project_duration": timeline.project_duration,
            "critical_path": [str(t) for t in timeline.critical_path],
            "schedules": [
                {
                    "task_id": str(s.task_id),
                    "earliest_start": s.earliest_start,
                    "earliest_finish": s.earliest_finish,
                    "slack": s.slack,
                    "is_critical": s.is_critical,
                }
                for s in timeline.schedules
            ],
        },
    }


async def materialize_metrics(
    session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID
) -> dict:
    """Persist current project + agent metrics as snapshot rows."""
    dash = await project_dashboard(session, org_id=org_id, project_id=project_id)
    project_count = 0
    for metric, value in dash["metrics"].items():
        session.add(
            ProjectMetric(organization_id=org_id, project_id=project_id, metric=metric, value=value)
        )
        project_count += 1
    agent_count = 0
    for am in dash["agent_metrics"]:
        for metric, value in am["metrics"].items():
            session.add(
                AgentMetric(
                    organization_id=org_id,
                    agent_id=uuid.UUID(am["agent_id"]),
                    metric=metric,
                    value=value,
                    dimensions={"project_id": str(project_id)},
                )
            )
            agent_count += 1
    return {"project_metrics_written": project_count, "agent_metrics_written": agent_count}
