"""Dependency graph: cycle detection and topological ordering.

Generic over a hashable node id (UUID in practice). Pure and side-effect-free.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

NodeT = TypeVar("NodeT", bound=Hashable)


class CycleError(Exception):
    """Raised when the dependency graph contains a cycle.

    ``cycle`` is the list of nodes forming the offending loop (first == last).
    """

    def __init__(self, cycle: list):
        self.cycle = cycle
        super().__init__(f"dependency cycle detected: {' -> '.join(str(n) for n in cycle)}")


@dataclass
class DependencyGraph(Generic[NodeT]):
    """A directed graph where an edge predecessor -> successor means
    'successor depends on predecessor'."""

    _nodes: set[NodeT] = field(default_factory=set)
    _succ: dict[NodeT, set[NodeT]] = field(default_factory=dict)
    _pred: dict[NodeT, set[NodeT]] = field(default_factory=dict)

    def add_node(self, node: NodeT) -> None:
        if node not in self._nodes:
            self._nodes.add(node)
            self._succ.setdefault(node, set())
            self._pred.setdefault(node, set())

    def add_edge(self, predecessor: NodeT, successor: NodeT) -> None:
        if predecessor == successor:
            raise CycleError([predecessor, successor])
        self.add_node(predecessor)
        self.add_node(successor)
        self._succ[predecessor].add(successor)
        self._pred[successor].add(predecessor)

    @property
    def nodes(self) -> set[NodeT]:
        return set(self._nodes)

    def successors(self, node: NodeT) -> set[NodeT]:
        return set(self._succ.get(node, set()))

    def predecessors(self, node: NodeT) -> set[NodeT]:
        return set(self._pred.get(node, set()))

    def find_cycle(self) -> list[NodeT] | None:
        """Return a cycle as a node list (first==last) or None if acyclic.

        Iterative DFS with WHITE/GREY/BLACK coloring. When a back-edge to a GREY
        node is found, the active path reconstructs the offending loop.
        """
        WHITE, GREY, BLACK = 0, 1, 2
        color: dict[NodeT, int] = {n: WHITE for n in self._nodes}

        for root in self._nodes:
            if color[root] != WHITE:
                continue
            path: list[NodeT] = [root]
            visiting: list[tuple[NodeT, Iterable[NodeT]]] = [(root, iter(sorted_succ(self, root)))]
            color[root] = GREY
            while visiting:
                node, it = visiting[-1]
                advanced = False
                for nxt in it:
                    if color[nxt] == GREY:
                        idx = path.index(nxt)
                        return path[idx:] + [nxt]
                    if color[nxt] == WHITE:
                        color[nxt] = GREY
                        path.append(nxt)
                        visiting.append((nxt, iter(sorted_succ(self, nxt))))
                        advanced = True
                        break
                if not advanced:
                    color[node] = BLACK
                    path.pop()
                    visiting.pop()
        return None

    def topological_order(self) -> list[NodeT]:
        """Kahn's algorithm. Raises CycleError if the graph is not a DAG."""
        indeg: dict[NodeT, int] = {n: len(self._pred[n]) for n in self._nodes}
        # Deterministic ordering for stable output.
        ready = sorted((n for n, d in indeg.items() if d == 0), key=str)
        order: list[NodeT] = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for succ in sorted(self._succ[node], key=str):
                indeg[succ] -= 1
                if indeg[succ] == 0:
                    ready.append(succ)
            ready.sort(key=str)
        if len(order) != len(self._nodes):
            cycle = self.find_cycle() or []
            raise CycleError(cycle)
        return order


def sorted_succ(graph: DependencyGraph[NodeT], node: NodeT) -> list[NodeT]:
    """Deterministic successor iteration for reproducible cycle reports."""
    return sorted(graph.successors(node), key=str)


def build_graph(
    nodes: Iterable[NodeT], edges: Iterable[tuple[NodeT, NodeT]]
) -> DependencyGraph[NodeT]:
    """Convenience constructor: add all nodes then all (pred, succ) edges."""
    g: DependencyGraph[NodeT] = DependencyGraph()
    for n in nodes:
        g.add_node(n)
    for pred, succ in edges:
        g.add_edge(pred, succ)
    return g
