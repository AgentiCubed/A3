"""Capability-based agent matching."""

from __future__ import annotations

from app.services.matching import AgentProfile, match_agents


def test_full_cover_beats_partial():
    agents = [
        AgentProfile("a", "Generalist", True, {"research.web": 3}),
        AgentProfile("b", "Specialist", True, {"research.web": 4, "writing.brief": 5}),
    ]
    ranked = match_agents(["research.web", "writing.brief"], agents)
    assert ranked[0].agent_id == "b"
    assert ranked[0].eligible
    assert ranked[1].agent_id == "a"
    assert not ranked[1].eligible
    assert ranked[1].missing == ["writing.brief"]


def test_higher_proficiency_wins_when_both_cover():
    agents = [
        AgentProfile("a", "Junior", True, {"analysis.python": 2}),
        AgentProfile("b", "Senior", True, {"analysis.python": 5}),
    ]
    ranked = match_agents(["analysis.python"], agents)
    assert ranked[0].agent_id == "b"


def test_disabled_agent_is_not_eligible():
    agents = [
        AgentProfile("a", "Disabled", False, {"research.web": 5}),
        AgentProfile("b", "Active", True, {"research.web": 3}),
    ]
    ranked = match_agents(["research.web"], agents)
    assert ranked[0].agent_id == "b"
    assert ranked[0].eligible
    assert not ranked[1].eligible  # disabled, despite higher proficiency


def test_no_requirements_ranks_by_total_proficiency():
    agents = [
        AgentProfile("a", "Broad", True, {"research.web": 3, "writing.brief": 3}),
        AgentProfile("b", "Narrow", True, {"research.web": 4}),
    ]
    ranked = match_agents([], agents)
    assert ranked[0].agent_id == "a"  # higher total proficiency
    assert all(r.eligible for r in ranked)
