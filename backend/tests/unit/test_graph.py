"""Dependency graph: topological order and cycle detection."""

from __future__ import annotations

import pytest

from app.scheduling.graph import CycleError, DependencyGraph, build_graph


def test_topological_order_chain():
    g = build_graph(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert g.topological_order() == ["a", "b", "c"]


def test_topological_order_diamond_is_valid():
    g = build_graph(["a", "b", "c", "d"], [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")])
    order = g.topological_order()
    # a before b/c; b/c before d.
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")
    assert order.index("b") < order.index("d")
    assert order.index("c") < order.index("d")


def test_self_loop_rejected():
    g: DependencyGraph[str] = DependencyGraph()
    with pytest.raises(CycleError):
        g.add_edge("a", "a")


def test_cycle_detected():
    g = build_graph(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])
    cycle = g.find_cycle()
    assert cycle is not None
    assert cycle[0] == cycle[-1]  # closed loop
    assert set(cycle) == {"a", "b", "c"}


def test_topological_order_raises_on_cycle():
    g = build_graph(["a", "b"], [("a", "b"), ("b", "a")])
    with pytest.raises(CycleError):
        g.topological_order()


def test_acyclic_graph_has_no_cycle():
    g = build_graph(["a", "b", "c"], [("a", "b"), ("a", "c")])
    assert g.find_cycle() is None
