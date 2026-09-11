"""Execution states (the durable task lifecycle vocabulary).

The full transition machine is built in Phase 5 next to this module. The enum
lives here now because ``Task.status`` uses it from Phase 3 onward.
"""

from __future__ import annotations

from enum import StrEnum


class ExecutionState(StrEnum):
    PLANNED = "planned"
    READY = "ready"
    QUEUED = "queued"
    RUNNING = "running"
    EVALUATING = "evaluating"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


#: States from which no further automated progress happens without intervention.
TERMINAL_STATES: frozenset[ExecutionState] = frozenset(
    {ExecutionState.COMPLETED, ExecutionState.CANCELLED}
)

#: States considered "open" for scheduling/critical-path purposes.
ACTIVE_STATES: frozenset[ExecutionState] = frozenset(
    {
        ExecutionState.PLANNED,
        ExecutionState.READY,
        ExecutionState.QUEUED,
        ExecutionState.RUNNING,
        ExecutionState.EVALUATING,
        ExecutionState.AWAITING_APPROVAL,
        ExecutionState.BLOCKED,
    }
)
