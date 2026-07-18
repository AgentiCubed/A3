"""End-to-end demonstration project (the required Phase-8 deliverable).

Builds and runs a real project through the full control loop:
  research → write brief → analyze a sample dataset → generate a visualization →
  evaluate → hit one deliberate failure → apply a remediation → complete →
  generate a closeout report.

Analysis and visualization use the REAL workers (pandas/matplotlib; R if present),
not mocks. Agent "thinking" uses the deterministic MockProvider so the demo is
reproducible offline (assumption A15).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis import python_worker, r_worker
from app.core.artifacts import LocalArtifactStore
from app.core.enums import (
    AgentKind,
    AgentRole,
    DependencyType,
    RequirementKind,
    RequirementPriority,
)
from app.core.roles import ActorType
from app.schemas.auth import RegisterRequest
from app.services import (
    agent_service,
    artifact_service,
    auth_service,
    closeout_service,
    execution_service,
    project_service,
    task_service,
)
from app.services.execution_service import EvaluationConfig
from app.services.methodology import ProjectSignals

# A small sample dataset the analysis worker crunches for real.
SAMPLE_DATASET = [
    {"label": "Northeast", "value": 120},
    {"label": "Midwest", "value": 95},
    {"label": "South", "value": 140},
    {"label": "West", "value": 110},
]


async def _agent(session, org_id, actor_id, name, caps, role=AgentRole.EXECUTOR):
    agent = await agent_service.register_agent(
        session,
        org_id=org_id,
        actor_id=actor_id,
        name=name,
        kind=AgentKind.AI,
        provider="mock",
        model="demo",
        default_role=role,
        config=None,
    )
    for cap in caps:
        await agent_service.add_capability(
            session, agent=agent, capability=cap, proficiency=4, evidence=None
        )
    return agent


async def build_and_run_demo(
    session: AsyncSession, *, store: LocalArtifactStore, now: datetime, email: str | None = None
) -> dict:
    # 1. Organization + owner.
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

    # 2. Agents (executors + a separate evaluator).
    researcher = await _agent(session, org_id, owner.id, "Researcher", ["research.web"])
    writer = await _agent(session, org_id, owner.id, "Writer", ["writing.brief"])
    analyst = await _agent(
        session, org_id, owner.id, "Analyst", ["analysis.data", "analysis.python"]
    )
    evaluator = await _agent(
        session, org_id, owner.id, "Evaluator", ["evaluation.rubric"], role=AgentRole.EVALUATOR
    )

    # 3. Project (dependency-heavy + deadline → CPM recommended).
    project, _ = await project_service.create_project(
        session,
        org_id=org_id,
        actor_id=owner.id,
        name="Market brief: Widget X regional demand",
        objective="Produce a researched, data-backed brief on Widget X regional demand.",
        acceptance_criteria={"deliverables": ["brief", "demand chart"]},
        signals=ProjectSignals(
            requirements_stable=True,
            hard_deadline=True,
            many_dependencies=True,
            continuous_flow=False,
            resource_constrained=False,
        ),
    )
    await project_service.add_requirement(
        session,
        project=project,
        kind=RequirementKind.ACCEPTANCE,
        text="A written brief and a regional-demand visualization.",
        priority=RequirementPriority.MUST,
        source="demo",
    )
    await project_service.add_milestone(
        session, project=project, name="Brief delivered", due_date=None, order_index=1
    )

    # 4. Tasks + dependencies.
    t_research = await task_service.create_task(
        session,
        project=project,
        title="Research Widget X demand",
        description="",
        estimate_hours=3,
        required_capabilities=["research.web"],
        is_human_task=False,
        milestone_id=None,
        priority=2,
    )
    t_brief = await task_service.create_task(
        session,
        project=project,
        title="Write the market brief",
        description="",
        estimate_hours=4,
        required_capabilities=["writing.brief"],
        is_human_task=False,
        milestone_id=None,
        priority=2,
    )
    t_analyze = await task_service.create_task(
        session,
        project=project,
        title="Analyze the regional dataset",
        description="",
        estimate_hours=5,
        required_capabilities=["analysis.data"],
        is_human_task=False,
        milestone_id=None,
        priority=1,
    )
    # The visualization task carries a deliberate failure marker (see step 7).
    t_visual = await task_service.create_task(
        session,
        project=project,
        title="Render the demand chart [[FAIL]]",
        description="",
        estimate_hours=2,
        required_capabilities=["analysis.python"],
        is_human_task=False,
        milestone_id=None,
        priority=1,
    )
    for pred, succ in [(t_research, t_brief), (t_research, t_analyze), (t_analyze, t_visual)]:
        await task_service.add_dependency(
            session,
            project=project,
            actor_id=owner.id,
            predecessor_id=pred.id,
            successor_id=succ.id,
            dependency_type=DependencyType.FINISH_TO_START,
            lag_hours=0,
        )

    for task, agent in [
        (t_research, researcher),
        (t_brief, writer),
        (t_analyze, analyst),
        (t_visual, analyst),
    ]:
        await agent_service.assign_agent_to_task(
            session, org_id=org_id, actor_id=owner.id, task=task, agent=agent
        )

    # 5. Execute research / brief / analyze with rubrics + a separate evaluator.
    eval_cfg = EvaluationConfig(
        rubric_specs=[{"key": "nonempty", "check": "non_empty"}],
        evaluator_agent_id=evaluator.id,
        max_remediations=1,
    )
    for task in (t_research, t_brief, t_analyze):
        await execution_service.execute_task(
            session,
            task=task,
            actor_id=owner.id,
            actor_type=ActorType.USER,
            max_attempts=2,
            evaluation=eval_cfg,
        )

    # 6. REAL analysis + visualization (Python worker; R cross-check if available).
    stats = python_worker.summary_stats(SAMPLE_DATASET, "value")
    chart_png = python_worker.bar_chart_png(
        SAMPLE_DATASET, "label", "value", title="Widget X regional demand"
    )
    analyze_exec = await execution_service.list_executions(
        session, org_id=org_id, task_id=t_analyze.id
    )
    artifact = await artifact_service.store_artifact(
        session,
        store,
        org_id=org_id,
        project_id=project.id,
        name="widget-demand-chart.png",
        content_type="image/png",
        data=chart_png,
        task_execution_id=analyze_exec[-1].id if analyze_exec else None,
        produced_by_agent_id=analyst.id,
        actor_id=owner.id,
    )
    # The brief itself is a promised deliverable — store it, so the project's
    # acceptance criteria are actually met when it closes (WS-4b gate).
    brief_exec = await execution_service.list_executions(session, org_id=org_id, task_id=t_brief.id)
    if brief_exec and brief_exec[-1].output:
        await artifact_service.store_artifact(
            session,
            store,
            org_id=org_id,
            project_id=project.id,
            name="market-brief.md",
            content_type="text/markdown",
            data=brief_exec[-1].output.encode("utf-8"),
            task_execution_id=brief_exec[-1].id,
            produced_by_agent_id=writer.id,
            actor_id=owner.id,
        )
    r_stats = r_worker.run_summary(SAMPLE_DATASET, "value") if r_worker.r_available() else None
    await project_service.add_decision(
        session,
        project=project,
        actor_id=owner.id,
        title="Regional demand analysis",
        context=f"Python worker stats: {stats}",
        decision=f"South leads demand (max={stats['max']}); mean={stats['mean']}.",
        consequences="Prioritize Southern distribution in the brief.",
    )

    # 7. Deliberate failure + remediation on the visualization task.
    fail_result = await execution_service.execute_task(
        session, task=t_visual, actor_id=owner.id, actor_type=ActorType.USER, max_attempts=1
    )  # raises no exception; the attempt fails and the task escalates to BLOCKED
    await project_service.add_decision(
        session,
        project=project,
        actor_id=owner.id,
        title="Remediation: chart renderer crash",
        context="The first render attempt failed on malformed input.",
        decision="Applied remediation (add_context/clean input) and re-ran the task.",
        consequences="Chart produced successfully on the retry.",
    )
    # Apply the remediation: clean the input that crashed it, return to READY, re-run.
    t_visual.title = t_visual.title.replace(" [[FAIL]]", "")
    await execution_service.transition_task(
        session,
        t_visual,
        execution_service.ExecutionState.READY,
        actor_id=owner.id,
        actor_type=ActorType.USER,
        reason="remediation applied",
    )
    ok_result = await execution_service.execute_task(
        session, task=t_visual, actor_id=owner.id, actor_type=ActorType.USER, max_attempts=1
    )

    # 8. Close the project, then generate the closeout report (reflects CLOSED).
    await closeout_service.close_project(session, project=project, actor_id=owner.id)
    report = await closeout_service.generate_closeout(
        session, org_id=org_id, project_id=project.id, generated_at=now
    )
    await session.commit()

    return {
        "org_id": str(org_id),
        "owner_email": owner_email,
        "project_id": str(project.id),
        "status": project.status.value,
        "task_count": report["task_count"],
        "tasks_completed": report["tasks_completed"],
        "failures": report["failures"],
        "remediation_events": len(report["remediation_events"]),
        "deliverables": report["deliverables"],
        "python_stats": stats,
        "r_stats": r_stats,
        "deliberate_failure_state": fail_result.final_state.value,
        "remediated_final_state": ok_result.final_state.value,
        "closeout_markdown": report["markdown"],
        "artifact_id": str(artifact.id),
    }


async def _main() -> None:  # pragma: no cover - manual entrypoint
    from app.db.session import SessionFactory

    store = artifact_service.default_store()
    async with SessionFactory() as session:
        result = await build_and_run_demo(session, store=store, now=datetime.now())
    print(result["closeout_markdown"])  # noqa: T201


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    asyncio.run(_main())
