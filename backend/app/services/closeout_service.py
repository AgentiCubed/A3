"""Project closeout & retrospective (Module 13).

Generates a final report from the project's record — tasks, deliverables, the
failure/remediation history, risks, decisions, and metrics — and closes the
project. Read-only over the immutable execution/evaluation history.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
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
from app.orchestration.state_machine.machine import assert_transition
from app.orchestration.state_machine.states import ExecutionState
from app.services import (
    acceptance_boundary_service,
    acceptance_service,
    analytics_service,
    decomposition_service,
    governed_evidence_service,
    task_service,
)

_REMEDIATION_ACTIONS = ("remediation.selected", "task.escalated", "task.reassigned")
ProjectClosed = acceptance_boundary_service.ProjectClosed


class AcceptanceNotMet(Exception):
    """Closing was refused: acceptance criteria fail and were not acknowledged."""

    def __init__(
        self,
        report: acceptance_service.AcceptanceReport,
        *,
        acknowledgement_allowed: bool,
    ):
        self.report = report
        self.acknowledgement_allowed = acknowledgement_allowed
        super().__init__("acceptance criteria unmet")


class AcceptanceSnapshotChanged(Exception):
    """Acceptance evidence changed after evaluation but before final close."""


class GovernedProjectNotActive(Exception):
    """A governed project must be active before it can close."""


class GovernedPlanApprovalRequired(Exception):
    """A draft plan must be explicitly approved or rejected before close."""


class GovernedMaterializationInvalid(Exception):
    """The approved executable graph no longer matches its immutable provenance."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class PlanTasksIncomplete(Exception):
    """At least one approved plan task has not completed."""

    def __init__(self, tasks: list[dict]):
        self.tasks = tasks
        super().__init__("approved plan tasks are incomplete")


class PlanTaskEvidenceInvalid(Exception):
    """A completed governed task lacks passing evidence for its approved rubric."""

    def __init__(self, tasks: list[dict]):
        self.tasks = tasks
        super().__init__("approved plan task evidence is missing or invalid")


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
        ),
    )

    dashboard = await analytics_service.project_dashboard(
        session, org_id=org_id, project_id=project_id
    )
    failures = [e for e in executions if e.state.value == "failed"]
    if project is None:
        acceptance = {"evaluated": False, "satisfied": True, "results": []}
    elif project.status == ProjectStatus.CLOSED and isinstance(project.closure_acceptance, dict):
        # Closed projects report the exact immutable snapshot that authorized
        # closure rather than independently evaluating a later view.
        acceptance = dict(project.closure_acceptance)
    else:
        acceptance = (
            await acceptance_service.evaluate_project_acceptance(session, project=project)
        ).to_dict()

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
        "acceptance": acceptance,
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
    lines += ["", "## Acceptance criteria"]
    acc = r.get("acceptance", {})
    if not acc.get("evaluated"):
        lines.append("- (none defined)")
    else:
        for c in acc.get("results", []):
            mark = "met" if c["passed"] else f"UNMET — {c['notes']}"
            lines.append(f"- [{c['kind']}] {c['key']}: {mark}")
    return "\n".join(lines)


async def _commit_close_snapshot(
    session: AsyncSession,
    *,
    project: Project,
    acceptance_revision: int,
    acceptance_snapshot: dict,
) -> None:
    """Close only if the evaluated acceptance revision is still current."""
    closed_id = await session.scalar(
        update(Project)
        .where(
            Project.id == project.id,
            Project.organization_id == project.organization_id,
            Project.status == project.status,
            Project.acceptance_revision == acceptance_revision,
        )
        .values(
            status=ProjectStatus.CLOSED,
            closure_acceptance=acceptance_snapshot,
        )
        .returning(Project.id)
        .execution_options(synchronize_session=False)
    )
    if closed_id is None:
        raise AcceptanceSnapshotChanged()
    await session.refresh(project)


async def _cancel_open_legacy_tasks(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID | None,
    actor_type: ActorType,
) -> list[str]:
    """Leave a manually closed project with no queued or running work."""
    cancelled: list[str] = []
    for task in await task_service.list_tasks(session, project.id):
        if task.status in {ExecutionState.COMPLETED, ExecutionState.CANCELLED}:
            continue
        before = task.status
        assert_transition(before, ExecutionState.CANCELLED)
        task.status = ExecutionState.CANCELLED
        await record_audit(
            session,
            organization_id=task.organization_id,
            project_id=task.project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action="task.transition",
            entity_type="Task",
            entity_id=task.id,
            before={"status": before.value},
            after={"status": ExecutionState.CANCELLED.value, "reason": "project closed"},
        )
        cancelled.append(str(task.id))
    if cancelled:
        await session.flush()
    return cancelled


async def close_project(
    session: AsyncSession,
    *,
    project: Project,
    actor_id: uuid.UUID | None,
    actor_type: ActorType = ActorType.USER,
    acknowledge_unmet_criteria: bool = False,
) -> Project:
    """Close the project — gated by its acceptance criteria (WS-4b).

    Governed projects additionally require an active, intact approved graph,
    completed tasks with passing persisted-rubric evidence, and non-waivable
    project acceptance. Legacy manual projects retain explicit acknowledged
    abandonment, recorded in the audit trail.
    """
    try:
        acceptance_revision = await acceptance_boundary_service.lock_acceptance_for_close(
            session,
            project_id=project.id,
            org_id=project.organization_id,
        )
    except acceptance_boundary_service.ProjectNotFound as exc:
        raise GovernedMaterializationInvalid("project is missing") from exc
    await session.refresh(project)
    try:
        materialization = await decomposition_service.load_approved_materialization(
            session,
            project=project,
            require_executable_assignments=False,
        )
    except decomposition_service.PlanApprovalRequired as exc:
        raise GovernedPlanApprovalRequired() from exc
    except decomposition_service.MaterializationInvalid as exc:
        raise GovernedMaterializationInvalid(exc.reason) from exc

    if materialization is not None:
        if project.status != ProjectStatus.ACTIVE:
            raise GovernedProjectNotActive()
        incomplete = [
            {
                "task_key": task.source_plan_task_key,
                "task_id": str(task.id),
                "status": task.status.value,
            }
            for task in materialization.tasks
            if task.status != ExecutionState.COMPLETED
        ]
        if incomplete:
            raise PlanTasksIncomplete(incomplete)
        try:
            evaluation_ids = await governed_evidence_service.passing_evaluation_ids(
                session,
                materialization.tasks,
            )
        except governed_evidence_service.EvidenceInvalid as exc:
            raise PlanTaskEvidenceInvalid(exc.tasks) from exc
    else:
        evaluation_ids = None

    report = await acceptance_service.evaluate_project_acceptance(session, project=project)
    unmet = [r.key for r in report.unmet]
    if unmet and (materialization is not None or not acknowledge_unmet_criteria):
        raise AcceptanceNotMet(
            report,
            acknowledgement_allowed=materialization is None,
        )

    cancelled_task_ids = (
        []
        if materialization is not None
        else await _cancel_open_legacy_tasks(
            session,
            project=project,
            actor_id=actor_id,
            actor_type=actor_type,
        )
    )
    before = project.status.value
    acceptance_snapshot = {
        **report.to_dict(),
        "acceptance_revision": acceptance_revision,
    }
    await _commit_close_snapshot(
        session,
        project=project,
        acceptance_revision=acceptance_revision,
        acceptance_snapshot=acceptance_snapshot,
    )
    close_details = {
        "status": ProjectStatus.CLOSED.value,
        "acceptance_evaluated": report.evaluated,
        "acceptance_satisfied": report.satisfied,
        "acceptance_revision": acceptance_revision,
        "acceptance": acceptance_snapshot,
        "cancelled_task_ids": cancelled_task_ids,
        "unmet_criteria": unmet,
        "unmet_acknowledged": bool(unmet and acknowledge_unmet_criteria),
    }
    if materialization is not None:
        close_details.update(
            {
                "plan_id": str(materialization.plan.id),
                "all_plan_tasks_completed": True,
                "task_evaluation_ids": evaluation_ids,
            }
        )
    await record_audit(
        session,
        organization_id=project.organization_id,
        project_id=project.id,
        actor_type=actor_type,
        actor_id=actor_id,
        action="project.closed",
        entity_type="Project",
        entity_id=project.id,
        before={"status": before},
        after=close_details,
    )
    return project
