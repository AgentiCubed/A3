"""Human approval gates.

Deciding an approval is restricted to approvers/admins by the API (Action
APPROVAL_DECIDE). On a decision linked to a task awaiting approval, the task is
advanced: approve accepts the deliverable (COMPLETED); reject routes back to
READY for revision — never a silent proceed.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.enums import ApprovalStatus
from app.core.rbac import Actor
from app.models.approval import Approval
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service


class NotFound(Exception):
    pass


class AlreadyDecided(Exception):
    pass


async def list_approvals(
    session: AsyncSession,
    *,
    org_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    status: ApprovalStatus | None = None,
) -> list[Approval]:
    stmt = select(Approval).where(Approval.organization_id == org_id)
    if project_id is not None:
        stmt = stmt.where(Approval.project_id == project_id)
    if status is not None:
        stmt = stmt.where(Approval.status == status)
    return list((await session.execute(stmt.order_by(Approval.created_at))).scalars().all())


async def decide_approval(
    session: AsyncSession,
    *,
    actor: Actor,
    approval_id: uuid.UUID,
    approve: bool,
    comment: str | None,
) -> Approval:
    approval = await session.get(Approval, approval_id)
    if approval is None or approval.organization_id != actor.organization_id:
        raise NotFound("approval")
    if approval.status != ApprovalStatus.PENDING:
        raise AlreadyDecided()

    approval.status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
    approval.decided_by = actor.user_id
    approval.decided_at = datetime.now(UTC)
    approval.comment = comment

    await record_audit(
        session,
        organization_id=actor.organization_id,
        actor_type=actor.actor_type,
        actor_id=actor.user_id,
        action="approval.decided",
        entity_type="Approval",
        entity_id=approval.id,
        after={"status": approval.status.value, "comment": comment},
    )

    # Advance the linked task if it is waiting on this gate.
    if approval.task_execution_id is not None:
        execution = await session.get(TaskExecution, approval.task_execution_id)
        if execution is not None:
            task = await session.get(Task, execution.task_id)
            if task is not None and task.status == ExecutionState.AWAITING_APPROVAL:
                target = ExecutionState.COMPLETED if approve else ExecutionState.READY
                await execution_service.transition_task(
                    session,
                    task,
                    target,
                    actor_id=actor.user_id,
                    actor_type=actor.actor_type,
                    reason="approval " + ("approved" if approve else "rejected"),
                )
    return approval
