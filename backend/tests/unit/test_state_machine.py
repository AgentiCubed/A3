"""Execution state-machine transition rules."""

from __future__ import annotations

import pytest

from app.orchestration.state_machine.machine import (
    IllegalTransition,
    assert_transition,
    can_transition,
    is_terminal,
)
from app.orchestration.state_machine.states import ExecutionState as S


def test_happy_path_transitions_are_legal():
    assert can_transition(S.PLANNED, S.READY)
    assert can_transition(S.READY, S.QUEUED)
    assert can_transition(S.QUEUED, S.RUNNING)
    assert can_transition(S.RUNNING, S.COMPLETED)
    assert can_transition(S.RUNNING, S.EVALUATING)
    assert can_transition(S.EVALUATING, S.COMPLETED)


def test_retry_and_escalation_transitions_are_legal():
    assert can_transition(S.RUNNING, S.FAILED)
    assert can_transition(S.FAILED, S.QUEUED)  # retry
    assert can_transition(S.FAILED, S.BLOCKED)  # escalate
    assert can_transition(S.BLOCKED, S.READY)  # reassign/resume


def test_terminal_states_have_no_exits():
    assert is_terminal(S.COMPLETED)
    assert is_terminal(S.CANCELLED)
    assert not can_transition(S.COMPLETED, S.RUNNING)
    assert not can_transition(S.CANCELLED, S.READY)


def test_illegal_transitions_rejected():
    assert not can_transition(S.PLANNED, S.RUNNING)  # must pass through READY/QUEUED
    assert not can_transition(S.COMPLETED, S.FAILED)
    with pytest.raises(IllegalTransition):
        assert_transition(S.PLANNED, S.COMPLETED)
