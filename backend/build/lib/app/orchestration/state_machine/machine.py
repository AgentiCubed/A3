"""Durable execution state machine.

Defines the legal transitions between execution states and a guard that rejects
illegal ones. The machine is engine-agnostic (no Celery/Temporal imports): the
worker layer drives it, but the rules live here so a different worker engine
cannot change them. See docs/execution-state-machine.md.
"""

from __future__ import annotations

from app.orchestration.state_machine.states import (
    TERMINAL_STATES,
    ExecutionState,
)

#: Legal transitions: state -> set of states reachable in one step.
TRANSITIONS: dict[ExecutionState, frozenset[ExecutionState]] = {
    ExecutionState.PLANNED: frozenset(
        {ExecutionState.READY, ExecutionState.BLOCKED, ExecutionState.CANCELLED}
    ),
    ExecutionState.READY: frozenset(
        {ExecutionState.QUEUED, ExecutionState.BLOCKED, ExecutionState.CANCELLED}
    ),
    ExecutionState.QUEUED: frozenset(
        {ExecutionState.RUNNING, ExecutionState.BLOCKED, ExecutionState.CANCELLED}
    ),
    ExecutionState.RUNNING: frozenset(
        {
            ExecutionState.EVALUATING,
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.AWAITING_APPROVAL,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.EVALUATING: frozenset(
        {
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.AWAITING_APPROVAL,
            ExecutionState.READY,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.AWAITING_APPROVAL: frozenset(
        {
            ExecutionState.RUNNING,
            ExecutionState.QUEUED,
            ExecutionState.READY,
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.FAILED: frozenset(
        {
            ExecutionState.READY,
            ExecutionState.QUEUED,
            ExecutionState.BLOCKED,
            ExecutionState.AWAITING_APPROVAL,
            ExecutionState.CANCELLED,
        }
    ),
    ExecutionState.BLOCKED: frozenset(
        {ExecutionState.READY, ExecutionState.QUEUED, ExecutionState.CANCELLED}
    ),
    ExecutionState.COMPLETED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
}


class IllegalTransition(Exception):
    def __init__(self, frm: ExecutionState, to: ExecutionState):
        self.frm = frm
        self.to = to
        super().__init__(f"illegal transition: {frm.value} -> {to.value}")


def can_transition(frm: ExecutionState, to: ExecutionState) -> bool:
    return to in TRANSITIONS.get(frm, frozenset())


def assert_transition(frm: ExecutionState, to: ExecutionState) -> None:
    if not can_transition(frm, to):
        raise IllegalTransition(frm, to)


def is_terminal(state: ExecutionState) -> bool:
    return state in TERMINAL_STATES
