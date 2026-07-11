"""Integration test: resumable persisted project run.

Session 1 — seed minimal data, start a run, commit, close.
Session 2 — reload from persistence, count executions, advance, commit, assert.

The test is designed to FAIL when:
- the first session does not commit (run_id won't be visible in session 2),
- no execution is created (count would not increase),
- more than one execution is created (count would increase by more than 1),
- execution raises unexpectedly (advance would propagate the error), or
- advance_project_run does not operate from persisted state (e.g. uses a
  cached in-memory object rather than reloading from the DB).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.core.enums import AgentKind, ProjectRunStatus
from app.models.agent import Agent
from app.models.organization import Organization
from app.models.project import Project
from app.models.project_run import ProjectRun
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.models.user import User
from app.orchestration.state_machine.states import ExecutionState
from app.services.project_run_service import advance_project_run, start_project_run
from tests.conftest import TestSessionFactory


@pytest.mark.asyncio
async def test_project_run_start_and_advance():
    # ------------------------------------------------------------------ #
    # Session 1: seed minimal fixtures, start the run, commit, then close #
    # ------------------------------------------------------------------ #
    async with TestSessionFactory() as s1:
        org = Organization(name="RunOrg", slug=f"run-org-{uuid.uuid4().hex[:8]}")
        s1.add(org)
        await s1.flush()

        user = User(
            organization_id=org.id,
            email=f"runner-{uuid.uuid4().hex[:8]}@example.com",
            hashed_password="x",
        )
        s1.add(user)
        await s1.flush()

        project = Project(
            organization_id=org.id,
            name="Minimal project",
            objective="run test",
            created_by=user.id,
        )
        s1.add(project)
        await s1.flush()

        agent = Agent(
            organization_id=org.id,
            name="MockAgent",
            kind=AgentKind.AI,
            provider="mock",
            model="demo",
        )
        s1.add(agent)
        await s1.flush()

        task = Task(
            organization_id=org.id,
            project_id=project.id,
            title="Do work",
            description="",
            estimate_hours=1.0,
            priority=1,
            status=ExecutionState.PLANNED,
            assigned_agent_id=agent.id,
        )
        s1.add(task)
        await s1.flush()

        run = await start_project_run(s1, project.id, user.id)

        # Retain identifiers before committing.
        run_id = run.id
        project_id = project.id
        task_id = task.id

        await s1.commit()
    # s1 is closed here.

    # ------------------------------------------------------------------ #
    # Session 2: reload from persistence, advance, assert                 #
    # ------------------------------------------------------------------ #
    async with TestSessionFactory() as s2:
        # Confirm the run is actually persisted.
        reloaded_run = await s2.get(ProjectRun, run_id)
        assert reloaded_run is not None, "run not found after session 1 commit"
        assert reloaded_run.project_id == project_id

        # Baseline execution count.
        count_stmt = select(func.count()).where(TaskExecution.task_id == task_id)
        count_before: int = (await s2.execute(count_stmt)).scalar_one()

        # Advance the run (reloads from DB internally).
        await advance_project_run(s2, run_id)
        await s2.flush()
        await s2.commit()

        count_after: int = (await s2.execute(count_stmt)).scalar_one()

    # Exactly one execution was created.
    assert (
        count_after - count_before == 1
    ), f"expected 1 new TaskExecution, got {count_after - count_before}"

    # The execution belongs to the expected task / project context.
    async with TestSessionFactory() as s3:
        exec_stmt = (
            select(TaskExecution)
            .where(TaskExecution.task_id == task_id)
            .order_by(TaskExecution.started_at)
        )
        executions = list((await s3.execute(exec_stmt)).scalars().all())
        assert len(executions) == 1
        exec_row = executions[0]
        assert exec_row.task_id == task_id

        # Verify the run persisted with the expected terminal status.
        final_run = await s3.get(ProjectRun, run_id)
        assert final_run is not None
        assert (
            final_run.status == ProjectRunStatus.COMPLETED
        ), f"expected COMPLETED, got {final_run.status}"
