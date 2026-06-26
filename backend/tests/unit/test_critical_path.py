"""Critical Path Method computation."""

from __future__ import annotations

import pytest

from app.scheduling.critical_path import Edge, TaskNode, compute_critical_path
from app.scheduling.graph import CycleError


def _tasks(**durations: float):
    return [TaskNode(id=k, duration=v) for k, v in durations.items()]


def test_classic_diamond_critical_path():
    # A(3) -> B(2), A(3) -> C(4), B -> D(2), C -> D
    tasks = _tasks(A=3, B=2, C=4, D=2)
    edges = [Edge("A", "B"), Edge("A", "C"), Edge("B", "D"), Edge("C", "D")]
    result = compute_critical_path(tasks, edges)

    assert result.project_duration == 9
    assert result.critical_path == ["A", "C", "D"]

    sched = result.schedules
    assert sched["A"].earliest_start == 0 and sched["A"].earliest_finish == 3
    assert sched["C"].earliest_start == 3 and sched["C"].earliest_finish == 7
    assert sched["D"].earliest_start == 7 and sched["D"].earliest_finish == 9
    # B is off the critical path with 2h of slack.
    assert sched["B"].slack == 2
    assert not sched["B"].is_critical
    assert sched["A"].is_critical and sched["C"].is_critical and sched["D"].is_critical


def test_lag_shifts_successor():
    tasks = _tasks(A=3, B=2)
    result = compute_critical_path(tasks, [Edge("A", "B", lag=1)])
    assert result.schedules["B"].earliest_start == 4  # 3 + 1 lag
    assert result.project_duration == 6


def test_single_task():
    result = compute_critical_path(_tasks(A=5), [])
    assert result.project_duration == 5
    assert result.critical_path == ["A"]


def test_parallel_independent_tasks():
    result = compute_critical_path(_tasks(A=5, B=3), [])
    assert result.project_duration == 5
    # Only the longest task is critical.
    assert result.critical_path == ["A"]
    assert result.schedules["B"].slack == 2


def test_cycle_raises():
    with pytest.raises(CycleError):
        compute_critical_path(_tasks(A=1, B=1), [Edge("A", "B"), Edge("B", "A")])


def test_unknown_edge_rejected():
    with pytest.raises(ValueError):
        compute_critical_path(_tasks(A=1), [Edge("A", "Z")])
