"""Rule-based methodology recommendation (Module 2).

Pure heuristics over a few project attributes. Deterministic and testable; can be
upgraded to model-assisted later (assumption A10). Returns the methodology plus a
human-readable rationale and a starter config.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import Methodology


@dataclass(frozen=True)
class ProjectSignals:
    requirements_stable: bool  # are requirements fixed up front?
    hard_deadline: bool  # is there a fixed external deadline?
    many_dependencies: bool  # heavy inter-task dependency structure?
    continuous_flow: bool  # steady stream of small items vs. a bounded effort?
    resource_constrained: bool  # shared/limited specialist agents (buffer mgmt)?


@dataclass(frozen=True)
class Recommendation:
    methodology: Methodology
    rationale: str
    config: dict


def recommend_methodology(s: ProjectSignals) -> Recommendation:
    """Pick a methodology from project signals.

    Order matters: the first matching rule wins, most-specific first.
    """
    if s.resource_constrained and s.many_dependencies and s.hard_deadline:
        return Recommendation(
            Methodology.CCPM,
            "Hard deadline with heavy dependencies under constrained specialist "
            "capacity: Critical Chain manages resource contention and buffers.",
            {"feeding_buffer_pct": 50, "project_buffer_pct": 50},
        )
    if s.many_dependencies and s.hard_deadline:
        return Recommendation(
            Methodology.CPM,
            "Dependency-heavy plan with a fixed deadline: Critical Path Method "
            "surfaces the schedule-driving chain and slack.",
            {"track_slack": True},
        )
    if s.requirements_stable and not s.continuous_flow:
        return Recommendation(
            Methodology.WATERFALL,
            "Stable, fully-specified requirements with a bounded effort: phased "
            "Waterfall is predictable and low-overhead.",
            {"phases": ["requirements", "design", "build", "verify", "release"]},
        )
    if s.continuous_flow:
        return Recommendation(
            Methodology.KANBAN,
            "Continuous flow of small, loosely-coupled items: Kanban with WIP "
            "limits optimizes throughput.",
            {"wip_limits": {"in_progress": 3, "review": 2}},
        )
    if not s.requirements_stable:
        return Recommendation(
            Methodology.SCRUM,
            "Evolving requirements benefit from time-boxed iteration and feedback: "
            "Scrum with fixed-length sprints.",
            {"sprint_length_days": 14},
        )
    return Recommendation(
        Methodology.HYBRID,
        "Mixed signals: a hybrid of iterative delivery with milestone gating.",
        {"iterations": True, "milestone_gates": True},
    )
