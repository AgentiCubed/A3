"""Project closeout & retrospective (Module 13).

Generates a final report from the project's record — tasks, deliverables, the
failure/remediation history, risks, decisions, and metrics — and closes the
project. Read-only over the immutable execution/evaluation history.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import ProjectStatus
from app.core.roles import ActorType
from app.models.artifact import Artifact
from app.models.audit_event import AuditEvent
from app.models.evaluation import Evaluation
from app.models.project import Project
from app.models.risk import Decision, Risk
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.services import analytics_service, task_service

_REMEDIATION_ACTIONS = ("remediation.selected", "task.escalated", "task.reassigned")


async def _scalars(session: AsyncSession, stmt):
    return list((await session.execute(stmt)).scalars().all())


async def generate_closeout(
    session: AsyncSession, *, org_id: uuid.UUID, project_id: uuid.UUID, generated_at: datetime
) -> dict:
    project = await session.get(Project, project_id)
    tasks = await task_service.list_tasks(session, project_id)
    executions = await _scalars(
        session,
        select(TaskExecution)
        .join(Task, TaskExecution.task_id == Task.id)
        .where(Task.project_id == project_id),
    )
    evaluations = await _scalars(
        session,
        select(Evaluation)
        .join(TaskExecution, Evaluation.task_execution_id == TaskExecution.id)
        .join(Task, TaskExecution.task_id == Task.id)
        .where(Task.project_id == project_id),
    )
    risks = await _scalars(session, select(Risk).where(Risk.project_id == project_id))
    decisions = await _scalars(session, select(Decision).where(Decision.project_id == project_id))
    artifacts = await _scalars(session, select(Artifact).where(Artifact.project_id == project_id))
    remediations = await _scalars(
        session,
        select(AuditEvent).where(
            AuditEvent.organization_id == org_id,
            AuditEvent.action.in_(_REMEDIATION_ACTIONS),
            AuditEvent.entity_id.in_(
                {t.id for t in tasks} | {e.id for e in executions}
            ),
        ),
    )

    dashboard = await analytics_service.project_dashboard(
        session, org_id=org_id, project_id=project_id
    )
    failures = [e for e in executions if e.state.value == "failed"]

    report = {
        "project_id": str(project_id),
        "name": project.name if project else "",
        "objective": project.objective if project else "",
        "status": project.status.value if project else "",
        "generated_at": generated_at.isoformat(),
        "metrics": dashboard["metrics"],
        "task_count": len(tasks),
        "tasks_completed": sum(1 for t in tasks if t.status.value == "completed"),
        "execution_attempts": len(executions),
        "failures": len(failures),
        "remediation_events": [{"action": r.action, "detail": r.after} for r in remediations],
        "evaluations": len(evaluations),
        "deliverables": [
            {"name": a.name, "content_type": a.content_type, "sha256": a.sha256} for a in artifacts
        ],
        "open_risks": [
            {"title": r.title, "severity": r.severity} for r in risks if r.status.value != "closed"
        ],
        "decisions": [{"title": d.title, "decision": d.decision} for d in decisions],
        "timeline": dashboard["timeline"],
    }
    report["markdown"] = _markdown(report)
    return report


def _markdown(r: dict) -> str:
    lines = [
        f"# Closeout report — {r['name']}",
        "",
        f"**Objective:** {r['objective']}",
        f"**Status:** {r['status']}  ·  **Generated:** {r['generated_at']}",
        "",
        "## Outcome",
        f"- Tasks: {r['tasks_completed']}/{r['task_count']} completed",
        f"- Execution attempts: {r['execution_attempts']} ({r['failures']} failed)",
        f"- Evaluations recorded: {r['evaluations']}",
        f"- Completion rate: {r['metrics'].get('completion_rate', 0)}",
        f"- Avg evaluation score: {r['metrics'].get('avg_evaluation_score', 0)}",
        "",
        "## Failures & remediation",
        f"- {r['failures']} failed execution attempt(s); "
        f"{len(r['remediation_events'])} remediation/escalation event(s).",
    ]
    for ev in r["remediation_events"]:
        lines.append(f"  - {ev['action']}: {ev['detail']}")
    lines += ["", "## Deliverables"]
    if r["deliverables"]:
        for d in r["deliverables"]:
            lines.append(f"- {d['name']} ({d['content_type']}, sha256={d['sha256'][:12]}…)")
    else:
        lines.append("- (none)")
    lines += ["", "## Open risks"]
    lines += [f"- {x['title']} (severity {x['severity']})" for x in r["open_risks"]] or ["- (none)"]
    lines += ["", "## Decisions"]
    lines += [f"- {d['title']}: {d['decision']}" for d in r["decisions"]] or ["- (none)"]
    return "\n".join(lines)


async def close_project(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
) -> Project:
    before = project.status.value
    project.status = ProjectStatus.CLOSED
    await record_audit(
        session,
        organization_id=project.organization_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="project.closed",
        entity_type="Project",
        entity_id=project.id,
        before={"status": before},
        after={"status": ProjectStatus.CLOSED.value},
    )
    return project
