"""Exactly-once approval decisions under concurrent deciders (ADR 0008)."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace

from app.core.enums import ApprovalStatus
from app.core.rbac import Actor
from app.core.roles import ActorType
from app.models.approval import Approval
from app.services import approval_service


@dataclass
class _SharedStatus:
    value: ApprovalStatus
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def compare_and_set(self, expected: ApprovalStatus, to: ApprovalStatus) -> int:
        async with self.lock:
            await asyncio.sleep(0)
            if self.value != expected:
                return 0
            self.value = to
            return 1


class _AtomicSession:
    """Models the database's conditional-UPDATE arbitration for one gate row."""

    def __init__(self, shared: _SharedStatus, *, to: ApprovalStatus) -> None:
        self.shared = shared
        self.to = to

    async def execute(self, statement):
        rowcount = await self.shared.compare_and_set(ApprovalStatus.PENDING, self.to)
        return SimpleNamespace(rowcount=rowcount)

    async def refresh(self, approval: Approval) -> None:
        approval.status = self.shared.value


def _pending_approval(approval_id: uuid.UUID, org_id: uuid.UUID) -> Approval:
    return Approval(
        id=approval_id,
        organization_id=org_id,
        project_id=uuid.uuid4(),
        # No linked execution: the race under test is the decision claim
        # itself; task advancement only runs for the single claim winner.
        task_execution_id=None,
        requested_action="task.complete",
        status=ApprovalStatus.PENDING,
    )


async def test_concurrent_deciders_record_exactly_one_decision(monkeypatch):
    """One approver and one rejecter race: one decision, one refusal."""
    shared = _SharedStatus(ApprovalStatus.PENDING)
    approval_id = uuid.uuid4()
    org_id = uuid.uuid4()
    approvals = [
        _pending_approval(approval_id, org_id),
        _pending_approval(approval_id, org_id),
    ]
    sessions = [
        _AtomicSession(shared, to=ApprovalStatus.APPROVED),
        _AtomicSession(shared, to=ApprovalStatus.REJECTED),
    ]
    actors = [
        Actor(
            actor_type=ActorType.USER,
            organization_id=org_id,
            user_id=uuid.uuid4(),
        )
        for _ in range(2)
    ]
    audits: list[dict] = []

    async def _record_audit(*args, **kwargs):
        audits.append(kwargs)

    async def _get_by_org(session, model, obj_id, org):
        # Each racer holds its own already-loaded PENDING snapshot of the gate,
        # exactly the read-then-write hazard the conditional UPDATE defends.
        return approvals[sessions.index(session)]

    monkeypatch.setattr(approval_service, "record_audit", _record_audit)
    monkeypatch.setattr(approval_service, "get_by_org", _get_by_org)

    outcomes = await asyncio.gather(
        *(
            approval_service.decide_approval(
                session,
                actor=actor,
                approval_id=approval_id,
                approve=(decision == ApprovalStatus.APPROVED),
                comment="racing decision",
            )
            for session, actor, decision in zip(
                sessions,
                actors,
                (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED),
                strict=True,
            )
        ),
        return_exceptions=True,
    )

    wins = [o for o in outcomes if isinstance(o, Approval)]
    refusals = [o for o in outcomes if isinstance(o, approval_service.AlreadyDecided)]
    assert len(wins) == 1
    assert len(refusals) == 1
    # The persisted state carries the winner's verdict and both in-memory
    # snapshots agree with it after the loser's refresh.
    assert shared.value in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
    assert wins[0].status == shared.value
    assert all(approval.status == shared.value for approval in approvals)
    assert len(audits) == 1
    assert audits[0]["after"]["status"] == shared.value.value
