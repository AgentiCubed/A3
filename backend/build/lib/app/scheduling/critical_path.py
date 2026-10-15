"""Critical Path Method (CPM) with all four PMI dependency relations.

Each task has a start S and finish F = S + duration. Every dependency edge
(predecessor p → successor s, lag L) imposes a constraint by relation:

- finish_to_start (FS):  s.start  >= p.finish + L
- start_to_start  (SS):  s.start  >= p.start  + L
- finish_to_finish (FF): s.finish >= p.finish + L
- start_to_finish (SF):  s.finish >= p.start  + L

The forward pass derives earliest start/finish (ES/EF); the backward pass derives
latest start/finish (LS/LF); slack = LS - ES; the critical path is the zero-slack
chain. Durations are in hours; missing/None durations count as 0.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

from app.scheduling.graph import DependencyGraph

NodeT = TypeVar("NodeT", bound=Hashable)

FINISH_TO_START = "finish_to_start"
START_TO_START = "start_to_start"
FINISH_TO_FINISH = "finish_to_finish"
START_TO_FINISH = "start_to_finish"


@dataclass(frozen=True)
class TaskNode(Generic[NodeT]):
    id: NodeT
    duration: float


@dataclass(frozen=True)
class Edge(Generic[NodeT]):
    predecessor: NodeT
    successor: NodeT
    lag: float = 0.0
    dep_type: str = FINISH_TO_START


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


def _forward_lower_bound(
    dep_type: str, es_p: float, ef_p: float, lag: float, dur_s: float
) -> float:
    """Lower bound on the successor's START implied by one incoming edge."""
    if dep_type == START_TO_START:
        return es_p + lag
    if dep_type == FINISH_TO_FINISH:
        return ef_p + lag - dur_s
    if dep_type == START_TO_FINISH:
        return es_p + lag - dur_s
    return ef_p + lag  # finish_to_start (default)


def _backward_upper_bound(
    dep_type: str, ls_s: float, lf_s: float, lag: float, dur_n: float
) -> float:
    """Upper bound on the predecessor's FINISH implied by one outgoing edge."""
    if dep_type == START_TO_START:
        return ls_s - lag + dur_n
    if dep_type == FINISH_TO_FINISH:
        return lf_s - lag
    if dep_type == START_TO_FINISH:
        return lf_s - lag + dur_n
    return ls_s - lag  # finish_to_start (default)


def compute_critical_path(
    tasks: Iterable[TaskNode[NodeT]], edges: Iterable[Edge[NodeT]]
) -> CriticalPathResult[NodeT]:
    """Compute CPM schedules. Raises ``CycleError`` if dependencies form a loop."""
    duration: dict[NodeT, float] = {t.id: max(0.0, float(t.duration)) for t in tasks}

    graph: DependencyGraph[NodeT] = DependencyGraph()
    for tid in duration:
        graph.add_node(tid)
    incoming: dict[NodeT, list[Edge[NodeT]]] = {tid: [] for tid in duration}
    outgoing: dict[NodeT, list[Edge[NodeT]]] = {tid: [] for tid in duration}
    for e in edges:
        if e.predecessor not in duration or e.successor not in duration:
            raise ValueError("edge references unknown task")
        graph.add_edge(e.predecessor, e.successor)
        incoming[e.successor].append(e)
        outgoing[e.predecessor].append(e)

    order = graph.topological_order()  # raises CycleError on a loop

    # Forward pass.
    es: dict[NodeT, float] = {}
    ef: dict[NodeT, float] = {}
    for node in order:
        bounds = [
            _forward_lower_bound(
                e.dep_type, es[e.predecessor], ef[e.predecessor], e.lag, duration[node]
            )
            for e in incoming[node]
        ]
        es[node] = max([0.0, *bounds])
        ef[node] = es[node] + duration[node]

    project_duration = max(ef.values(), default=0.0)

    # Backward pass.
    ls: dict[NodeT, float] = {}
    lf: dict[NodeT, float] = {}
    for node in reversed(order):
        bounds = [
            _backward_upper_bound(
                e.dep_type, ls[e.successor], lf[e.successor], e.lag, duration[node]
            )
            for e in outgoing[node]
        ]
        lf[node] = min([project_duration, *bounds])
        ls[node] = lf[node] - duration[node]

    schedules: dict[NodeT, Schedule] = {
        node: Schedule(
            earliest_start=es[node],
            earliest_finish=ef[node],
            latest_start=ls[node],
            latest_finish=lf[node],
            slack=ls[node] - es[node],
        )
        for node in order
    }
    critical_path = [n for n in order if schedules[n].is_critical]
    return CriticalPathResult(
        schedules=schedules, critical_path=critical_path, project_duration=project_duration
    )
