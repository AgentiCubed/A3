"""Human approval gates.

Deciding an approval is restricted to approvers/admins by the API (Action
APPROVAL_DECIDE). On a decision linked to a task awaiting approval, the task is
advanced. Legacy manual work can still be accepted as complete; governed work
always returns to READY because its approved rubric must pass on reevaluation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.core.audit import record_audit
from app.core.enums import ApprovalStatus
from app.core.rbac import Actor
from app.db.queries import get_by_org
from app.models.approval import Approval
from app.models.task import Task
from app.models.task_execution import TaskExecution
from app.orchestration.state_machine.states import ExecutionState
from app.services import execution_service
from app.services.errors import NotFound


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
    approval = await get_by_org(session, Approval, approval_id, actor.organization_id)
    if approval is None:
        raise NotFound("approval")
    if approval.status != ApprovalStatus.PENDING:
        raise AlreadyDecided()

    # Exactly-once decision: a plain ORM assignment is read-then-write, so two
    # concurrent deciders could both pass the PENDING check and both record a
    # decision (with the linked task transitioning twice). The conditional
    # UPDATE makes the persisted PENDING state the arbiter — the same claim
    # pattern as the governed dispatch spine (ADR 0008).
    new_status = ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
    decided_at = datetime.now(UTC)
    result = await session.execute(
        update(Approval)
        .where(
            Approval.id == approval.id,
            Approval.organization_id == actor.organization_id,
            Approval.status == ApprovalStatus.PENDING,
        )
        .values(
            status=new_status,
            decided_by=actor.user_id,
            decided_at=decided_at,
            comment=comment,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        await session.refresh(approval)
        raise AlreadyDecided()
    set_committed_value(approval, "status", new_status)
    set_committed_value(approval, "decided_by", actor.user_id)
    set_committed_value(approval, "decided_at", decided_at)
    set_committed_value(approval, "comment", comment)

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
                governed = task.source_plan_id is not None
                if governed:
                    target = ExecutionState.READY
                    reason = (
                        "governed remediation approved; passing reevaluation required"
                        if approve
                        else "governed remediation rejected; passing reevaluation required"
                    )
                else:
                    target = ExecutionState.COMPLETED if approve else ExecutionState.READY
                    reason = "approval " + ("approved" if approve else "rejected")
                await execution_service.transition_task(
                    session,
                    task,
                    target,
                    actor_id=actor.user_id,
                    actor_type=actor.actor_type,
                    reason=reason,
                )
    return approval
