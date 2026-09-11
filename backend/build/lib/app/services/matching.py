"""Capability-based agent matching (pure).

Given a task's required capabilities and a set of agent profiles, rank the
agents. An agent is *eligible* if it is active and covers every required
capability; eligible agents sort ahead of partial matches. Within a tier, rank
by coverage then summed proficiency of the matched capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentProfile:
    agent_id: object
    name: str
    is_active: bool
    capabilities: dict[str, int] = field(default_factory=dict)  # capability -> proficiency (1-5)


@dataclass(frozen=True)
class MatchResult:
    agent_id: object
    name: str
    eligible: bool
    coverage: float
    matched: list[str]
    missing: list[str]
    score: float


def match_agents(required: list[str], agents: list[AgentProfile]) -> list[MatchResult]:
    required_set = list(dict.fromkeys(required))  # de-dupe, preserve order
    results: list[MatchResult] = []

    for agent in agents:
        matched = [c for c in required_set if c in agent.capabilities]
        missing = [c for c in required_set if c not in agent.capabilities]
        coverage = 1.0 if not required_set else len(matched) / len(required_set)
        proficiency_sum = sum(agent.capabilities.get(c, 0) for c in matched)
        # When nothing is required, score by total declared proficiency.
        if not required_set:
            proficiency_sum = sum(agent.capabilities.values())
        eligible = agent.is_active and not missing
        results.append(
            MatchResult(
                agent_id=agent.agent_id,
                name=agent.name,
                eligible=eligible,
                coverage=coverage,
                matched=matched,
                missing=missing,
                score=float(proficiency_sum),
            )
        )

    results.sort(key=lambda r: (r.eligible, r.coverage, r.score), reverse=True)
    return results
