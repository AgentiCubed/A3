"""Atomic dispatch claims for plan-derived tasks."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace

from app.core.roles import ActorType
from app.models.task import Task
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service


@dataclass
class _SharedStatus:
    value: ExecutionState
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def compare_and_set(self, expected: ExecutionState, to: ExecutionState) -> int:
        async with self.lock:
            await asyncio.sleep(0)
            if self.value != expected:
                return 0
            self.value = to
            return 1


class _AtomicSession:
    def __init__(
        self,
        shared: _SharedStatus,
        *,
        expected: ExecutionState,
        to: ExecutionState,
    ) -> None:
        self.shared = shared
        self.expected = expected
        self.to = to
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        rowcount = await self.shared.compare_and_set(self.expected, self.to)
        return SimpleNamespace(rowcount=rowcount)

    async def refresh(self, task: Task) -> None:
        task.status = self.shared.value


def _governed_task(task_id: uuid.UUID, status: ExecutionState) -> Task:
    return Task(
        id=task_id,
        organization_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        source_plan_id=uuid.uuid4(),
        source_plan_task_key="work",
        title="Governed work",
        status=status,
    )


async def test_duplicate_workers_have_exactly_one_governed_execution_claim(
    monkeypatch,
):
    shared = _SharedStatus(ExecutionState.QUEUED)
    task_id = uuid.uuid4()
    tasks = [
        _governed_task(task_id, ExecutionState.QUEUED),
        _governed_task(task_id, ExecutionState.QUEUED),
    ]
    sessions = [
        _AtomicSession(
            shared,
            expected=ExecutionState.QUEUED,
            to=ExecutionState.RUNNING,
        )
        for _ in range(2)
    ]
    audits: list[dict] = []

    async def _record_audit(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(execution_service, "record_audit", _record_audit)

    outcomes = await asyncio.gather(
        *(
            execution_service._claim_governed_execution(
                session,
                task,
                actor_id=None,
                actor_type=ActorType.SYSTEM,
            )
            for session, task in zip(sessions, tasks, strict=True)
        ),
        return_exceptions=True,
    )

    assert sum(outcome is None for outcome in outcomes) == 1
    assert sum(isinstance(outcome, execution_service.AlreadyQueued) for outcome in outcomes) == 1
    assert shared.value == ExecutionState.RUNNING
    assert all(task.status == ExecutionState.RUNNING for task in tasks)
    assert len(audits) == 1
    assert audits[0]["before"] == {"status": "queued"}
    assert audits[0]["after"] == {"status": "running", "reason": None}


async def test_concurrent_queue_requests_submit_only_one_governed_claim(monkeypatch):
    shared = _SharedStatus(ExecutionState.READY)
    task_id = uuid.uuid4()
    tasks = [
        _governed_task(task_id, ExecutionState.READY),
        _governed_task(task_id, ExecutionState.READY),
    ]
    sessions = [
        _AtomicSession(
            shared,
            expected=ExecutionState.READY,
            to=ExecutionState.QUEUED,
        )
        for _ in range(2)
    ]
    audits: list[dict] = []

    async def _record_audit(*args, **kwargs):
        audits.append(kwargs)

    monkeypatch.setattr(execution_service, "record_audit", _record_audit)

    outcomes = await asyncio.gather(
        *(
            execution_service._move_governed_to_queued(
                session,
                task,
                actor_id=None,
                actor_type=ActorType.SYSTEM,
            )
            for session, task in zip(sessions, tasks, strict=True)
        ),
        return_exceptions=True,
    )

    assert sum(outcome is None for outcome in outcomes) == 1
    assert sum(isinstance(outcome, execution_service.AlreadyQueued) for outcome in outcomes) == 1
    assert shared.value == ExecutionState.QUEUED
    assert all(task.status == ExecutionState.QUEUED for task in tasks)
    assert len(audits) == 1
    assert audits[0]["before"] == {"status": "ready"}
    assert audits[0]["after"] == {"status": "queued", "reason": None}
