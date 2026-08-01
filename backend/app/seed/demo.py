"""Auditable objective-to-close demonstration of the governed runtime.

The planner, executors, and evaluator use the deterministic ``mock`` adapter so
the orchestration proof is reproducible and offline. That adapter is not live
market research and the returned evidence says so explicitly. The statistics,
permissioned analysis-tool invocation, chart rendering, artifact persistence,
evaluation/remediation loop, and lifecycle gates are real application paths.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis import python_worker, r_worker
from app.core.artifacts import LocalArtifactStore
from app.core.enums import AgentKind, AgentRole, ToolKind, ToolSensitivity
from app.core.rbac import Actor
from app.core.roles import ActorType, SystemRole
from app.models.audit_event import AuditEvent
from app.schemas.auth import RegisterRequest
from app.schemas.decomposition import PlanTaskAssignmentIn
from app.services import (
    agent_service,
    artifact_service,
    auth_service,
    closeout_service,
    decomposition_service,
    evaluation_service,
    execution_service,
    project_service,
    scheduler_service,
    tool_service,
)
from app.services.methodology import ProjectSignals

AUTONOMOUS_DEMO_MARKER = "[[AUTONOMOUS_DEMO:DEMO_ACCEPTED]]"
DEMO_ACCEPTANCE_TOKEN = "DEMO_ACCEPTED"  # noqa: S105 - rubric token, not a credential
MOCK_DISCLOSURE = (
    "Planner, executor, and evaluator text was produced by the deterministic "
    "MockProvider for an offline orchestration demonstration; it is not live market research."
)

SAMPLE_DATASET = [
    {"label": "Northeast", "value": 120},
    {"label": "Midwest", "value": 95},
    {"label": "South", "value": 140},
    {"label": "West", "value": 110},
]


async def _agent(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    name: str,
    capabilities: list[str],
    role: AgentRole,
):
    agent = await agent_service.register_agent(
        session,
        org_id=org_id,
        actor_id=actor_id,
        name=name,
        kind=AgentKind.AI,
        provider="mock",
        model="deterministic-demo",
        default_role=role,
        config=None,
    )
    for capability in capabilities:
        await agent_service.add_capability(
            session,
            agent=agent,
            capability=capability,
            proficiency=4,
            evidence="offline governed-demo registration",
        )
    return agent


async def _audits(session: AsyncSession, *, org_id: uuid.UUID, action: str) -> list[AuditEvent]:
    rows = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.organization_id == org_id, AuditEvent.action == action)
        .order_by(AuditEvent.occurred_at, AuditEvent.id)
    )
    return list(rows.scalars().all())


async def build_and_run_demo(
    session: AsyncSession,
    *,
    store: LocalArtifactStore,
    now: datetime,
    email: str | None = None,
) -> dict:
    """Run one deterministic, governed project and return its persisted proof."""
    owner_email = email or f"demo-{uuid.uuid4().hex[:8]}@agenticubed.dev"
    owner = await auth_service.register_organization(
        session,
        RegisterRequest(
            organization_name="Demo Co",
            email=owner_email,
            password="demo-password-123",  # noqa: S106 - seed/demo credential
        ),
    )
    org_id = owner.organization_id

    planner = await _agent(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Demo Planner",
        capabilities=["planning.decompose"],
        role=AgentRole.EXECUTOR,
    )
    analyst = await _agent(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Demo Research Analyst",
        capabilities=[
            "research.market",
            "analysis.data",
            "analysis.python",
            "analysis.stats",
        ],
        role=AgentRole.EXECUTOR,
    )
    writer = await _agent(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Demo Brief Writer",
        capabilities=["writing.brief", "writing.report"],
        role=AgentRole.EXECUTOR,
    )
    evaluator = await _agent(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Demo Independent Evaluator",
        capabilities=["evaluation.rubric"],
        role=AgentRole.EVALUATOR,
    )

    analysis_tool = await tool_service.register_tool(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="analysis.summary_stats",
        kind=ToolKind.PYTHON_FN,
        description="Compute summary statistics over a supplied numeric dataset.",
        schema={
            "type": "object",
            "required": ["records", "value_column"],
            "properties": {
                "records": {"type": "array", "items": {"type": "object"}},
                "value_column": {"type": "string"},
            },
        },
        sensitivity=ToolSensitivity.LOW,
    )
    await tool_service.grant_tool_permission(
        session,
        actor=Actor(
            actor_type=ActorType.USER,
            organization_id=org_id,
            user_id=owner.id,
            system_role=SystemRole.OWNER,
        ),
        agent_id=analyst.id,
        tool_id=analysis_tool.id,
        scope=None,
        expires_at=None,
    )

    project, _ = await project_service.create_project(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Governed market brief: Widget X regional demand",
        objective=(
            "Produce a data-backed market brief and demand chart for Widget X regional demand. "
            f"Run the offline autonomous orchestration proof {AUTONOMOUS_DEMO_MARKER}."
        ),
        acceptance_criteria={"deliverables": ["market brief", "demand chart"]},
        signals=ProjectSignals(
            requirements_stable=True,
            hard_deadline=True,
            many_dependencies=True,
            continuous_flow=False,
            resource_constrained=False,
        ),
    )

    draft = await decomposition_service.generate_plan(
        session,
        project=project,
        planner_agent_id=planner.id,
        actor_id=owner.id,
    )
    if draft.plan_spec is None or draft.plan_spec_sha256 is None:
        raise RuntimeError(f"demo planner did not produce a valid draft: {draft.diagnostic}")
    draft_version = draft.version
    draft_sha256 = draft.plan_spec_sha256
    plan_task_keys = [task["key"] for task in draft.plan_spec["tasks"]]
    executor_by_key = {"research": analyst, "deliver": writer}
    if set(plan_task_keys) != set(executor_by_key):
        raise RuntimeError(f"unexpected autonomous demo task keys: {plan_task_keys}")
    assignments = [
        PlanTaskAssignmentIn(
            task_key=task_key,
            agent_id=executor_by_key[task_key].id,
            evaluator_agent_id=evaluator.id,
            max_remediations=1,
        )
        for task_key in plan_task_keys
    ]
    approved_plan, materialized_tasks, dependency_count = await decomposition_service.approve_plan(
        session,
        project=project,
        plan_id=draft.id,
        expected_version=draft_version,
        expected_plan_spec_sha256=draft_sha256,
        assignments=assignments,
        actor_id=owner.id,
        comment="Approved exact deterministic demo plan and agent assignments.",
    )
    # Approval provenance is executable authority, so make it durable before
    # the one governed start revalidates the plan.
    await session.commit()

    materialization = await decomposition_service.begin_project_execution(
        session, project=project, actor_id=owner.id
    )
    if materialization is None:
        raise RuntimeError("approved demo project was not recognized as governed")
    started_status = project.status.value
    await session.commit()

    outcomes = await scheduler_service.run_inline(
        session,
        project_id=project.id,
        actor_id=owner.id,
        actor_type=ActorType.USER,
        max_attempts=1,
        timeout_s=30,
    )
    key_by_id = {task.id: str(task.source_plan_task_key) for task in materialization.tasks}
    execution_order = [key_by_id[outcome.task_id] for outcome in outcomes]
    if len(outcomes) != len(materialization.tasks) or any(
        outcome.status.value != "completed" for outcome in outcomes
    ):
        raise RuntimeError("governed scheduler did not complete the approved demo graph")

    stats = python_worker.summary_stats(SAMPLE_DATASET, "value")
    chart_png = python_worker.bar_chart_png(
        SAMPLE_DATASET, "label", "value", title="Widget X regional demand"
    )
    r_stats = r_worker.run_summary(SAMPLE_DATASET, "value") if r_worker.r_available() else None

    tasks_by_key = {str(task.source_plan_task_key): task for task in materialized_tasks}
    executions_by_key = {
        key: await execution_service.list_executions(session, org_id=org_id, task_id=task.id)
        for key, task in tasks_by_key.items()
    }
    deliver_output = executions_by_key["deliver"][-1].output or ""
    brief_bytes = (
        "# Widget X regional-demand market brief\n\n"
        f"> Demonstration disclosure: {MOCK_DISCLOSURE}\n\n"
        "## Governed agent output\n\n"
        f"{deliver_output}\n\n"
        "## Real dataset analysis\n\n"
        f"- Mean demand: {stats['mean']}\n"
        f"- Total demand: {stats['sum']}\n"
        f"- Highest regional demand: {stats['max']}\n"
    ).encode()
    brief_artifact = await artifact_service.store_artifact(
        session,
        store,
        org_id=org_id,
        project_id=project.id,
        name="market-brief.md",
        content_type="text/markdown",
        data=brief_bytes,
        task_execution_id=executions_by_key["deliver"][-1].id,
        produced_by_agent_id=writer.id,
        actor_id=owner.id,
        actor_type=ActorType.USER,
    )
    chart_artifact = await artifact_service.store_artifact(
        session,
        store,
        org_id=org_id,
        project_id=project.id,
        name="demand-chart.png",
        content_type="image/png",
        data=chart_png,
        task_execution_id=executions_by_key["research"][-1].id,
        produced_by_agent_id=analyst.id,
        actor_id=owner.id,
        actor_type=ActorType.USER,
    )

    await closeout_service.close_project(
        session,
        project=project,
        actor_id=owner.id,
        actor_type=ActorType.USER,
        acknowledge_unmet_criteria=False,
    )
    report = await closeout_service.generate_closeout(
        session, org_id=org_id, project_id=project.id, generated_at=now
    )
    await session.flush()

    evaluations = []
    for key in execution_order:
        task_evaluations = await evaluation_service.list_evaluations_for_task(
            session, org_id=org_id, task_id=tasks_by_key[key].id
        )
        evaluations.append(
            {
                "task_key": key,
                "evaluation_ids": [str(item.id) for item in task_evaluations],
                "verdicts": [item.verdict.value for item in task_evaluations],
                "final_verdict": task_evaluations[-1].verdict.value,
                "rubric_sha256": task_evaluations[-1].rubric_sha256,
            }
        )

    approval_audits = await _audits(session, org_id=org_id, action="plan.approved")
    start_audits = await _audits(session, org_id=org_id, action="project.started")
    remediation_audits = await _audits(session, org_id=org_id, action="remediation.selected")
    tool_audits = await _audits(session, org_id=org_id, action="tool.invoked")
    close_audits = await _audits(session, org_id=org_id, action="project.closed")
    await session.commit()

    return {
        "org_id": str(org_id),
        "owner_email": owner_email,
        "project_id": str(project.id),
        "status": project.status.value,
        "task_count": report["task_count"],
        "tasks_completed": report["tasks_completed"],
        "execution_order": execution_order,
        "plan": {
            "id": str(approved_plan.id),
            "draft_created": True,
            "status": approved_plan.status.value,
            "version": approved_plan.version,
            "plan_spec_sha256": approved_plan.plan_spec_sha256,
            "approved_exact_sha256": draft_sha256,
            "task_keys": plan_task_keys,
            "materialized_task_ids": [str(task.id) for task in materialized_tasks],
            "dependency_count": dependency_count,
            "approval_audit_count": len(approval_audits),
        },
        "start": {
            "status_after_start": started_status,
            "audit_count": len(start_audits),
            "plan_id": (start_audits[0].after or {}).get("plan_id") if start_audits else None,
        },
        "evaluations": evaluations,
        "remediation": {
            "count": len(remediation_audits),
            "task_key": "deliver",
            "attempts": len(executions_by_key["deliver"]),
            "runtime_remediations": len(remediation_audits),
            "linked_attempts": sum(
                execution.remediation_of is not None for execution in executions_by_key["deliver"]
            ),
            "events": [audit.after for audit in remediation_audits],
        },
        "tool_invocations": [audit.after for audit in tool_audits],
        "artifacts": [
            {
                "id": str(brief_artifact.id),
                "name": brief_artifact.name,
                "content_type": brief_artifact.content_type,
                "sha256": brief_artifact.sha256,
                "storage_key": brief_artifact.storage_key,
            },
            {
                "id": str(chart_artifact.id),
                "name": chart_artifact.name,
                "content_type": chart_artifact.content_type,
                "sha256": chart_artifact.sha256,
                "storage_key": chart_artifact.storage_key,
            },
        ],
        "python_stats": stats,
        "r_stats": r_stats,
        "acceptance": report["acceptance"],
        "close": {
            "audit_count": len(close_audits),
            "details": close_audits[0].after if close_audits else None,
        },
        "mock_provider_disclosure": MOCK_DISCLOSURE,
        "analysis_mode": "real Python worker and permissioned analysis.summary_stats tool",
        "closeout_markdown": report["markdown"],
    }


async def _main(email: str | None = None) -> None:  # pragma: no cover - manual entrypoint
    from app.db.session import SessionFactory

    store = artifact_service.default_store()
    async with SessionFactory() as session:
        result = await build_and_run_demo(session, store=store, now=datetime.now(UTC), email=email)
    print(result["closeout_markdown"])  # noqa: T201


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import asyncio
    import os

    # The demo is a synchronous, offline orchestration proof. Force the
    # inline engine and in-memory bus for THIS PROCESS ONLY, regardless of
    # deployment settings — otherwise, under the compose stack
    # (WORKFLOW_ENGINE_BACKEND=celery), project start hands the task chain
    # to the worker container and the seed's run_inline pass races it,
    # finds nothing dispatchable, and aborts. The running api/worker
    # services are unaffected; they keep their own settings.
    os.environ["WORKFLOW_ENGINE_BACKEND"] = "inline"
    os.environ["EVENT_BUS_BACKEND"] = "memory"
    from app.core.config import get_settings
    from app.orchestration.adapters.event_bus import reset_event_bus
    from app.orchestration.engines import reset_workflow_engine

    get_settings.cache_clear()
    reset_workflow_engine()
    reset_event_bus()

    parser = argparse.ArgumentParser(description="Run the governed demo project")
    parser.add_argument(
        "--email",
        default=None,
        help=(
            "Owner email for the seeded demo organization (password: "
            "demo-password-123). Defaults to a random demo address."
        ),
    )
    args = parser.parse_args()
    asyncio.run(_main(email=args.email))
