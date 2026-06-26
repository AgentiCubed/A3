"""Critical Path Method (CPM).

Forward pass computes earliest start/finish; backward pass computes latest
start/finish; slack = LS - ES; the critical path is the zero-slack chain.

MVP scope: dependencies are treated as finish-to-start with an optional lag
(the dominant case). Other dependency types are accepted by the caller but
modeled as finish-to-start here; richer semantics are a documented follow-up
(see docs/issues). Durations are in hours; missing/None durations count as 0.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.scheduling.graph import DependencyGraph

NodeT = TypeVar("NodeT", bound=Hashable)


@dataclass(frozen=True)
class TaskNode(Generic[NodeT]):
    id: NodeT
    duration: float


@dataclass(frozen=True)
class Edge(Generic[NodeT]):
    predecessor: NodeT
    successor: NodeT
    lag: float = 0.0


@dataclass(frozen=True)
class Schedule:
    earliest_start: float
    earliest_finish: float
    latest_start: float
    latest_finish: float
    slack: float

    @property
    def is_critical(self) -> bool:
        return abs(self.slack) < 1e-9


@dataclass(frozen=True)
class CriticalPathResult(Generic[NodeT]):
    schedules: dict[NodeT, Schedule]
    critical_path: list[NodeT]
    project_duration: float


def compute_critical_path(
    tasks: Iterable[TaskNode[NodeT]], edges: Iterable[Edge[NodeT]]
) -> CriticalPathResult[NodeT]:
    """Compute CPM schedules. Raises ``CycleError`` if dependencies form a loop."""
    duration: dict[NodeT, float] = {t.id: max(0.0, float(t.duration)) for t in tasks}

    graph: DependencyGraph[NodeT] = DependencyGraph()
    for tid in duration:
        graph.add_node(tid)
    lag: dict[tuple[NodeT, NodeT], float] = {}
    for e in edges:
        if e.predecessor not in duration or e.successor not in duration:
            raise ValueError("edge references unknown task")
        graph.add_edge(e.predecessor, e.successor)
        # Largest lag wins if duplicated.
        key = (e.predecessor, e.successor)
        lag[key] = max(lag.get(key, e.lag), e.lag)

    order = graph.topological_order()  # raises CycleError on a loop

    # Forward pass.
    es: dict[NodeT, float] = {}
    ef: dict[NodeT, float] = {}
    for node in order:
        preds = graph.predecessors(node)
        es[node] = max((ef[p] + lag.get((p, node), 0.0) for p in preds), default=0.0)
        ef[node] = es[node] + duration[node]

    project_duration = max(ef.values(), default=0.0)

    # Backward pass.
    ls: dict[NodeT, float] = {}
    lf: dict[NodeT, float] = {}
    for node in reversed(order):
        succs = graph.successors(node)
        lf[node] = min((ls[s] - lag.get((node, s), 0.0) for s in succs), default=project_duration)
        ls[node] = lf[node] - duration[node]

    schedules: dict[NodeT, Schedule] = {}
    for node in order:
        slack = ls[node] - es[node]
        schedules[node] = Schedule(
            earliest_start=es[node],
            earliest_finish=ef[node],
            latest_start=ls[node],
            latest_finish=lf[node],
            slack=slack,
        )

    critical_path = [n for n in order if schedules[n].is_critical]
    return CriticalPathResult(
        schedules=schedules,
        critical_path=critical_path,
        project_duration=project_duration,
    )
