"""Rule-based methodology recommender."""

from __future__ import annotations

from app.core.enums import Methodology
from app.services.methodology import ProjectSignals, recommend_methodology


def _signals(**over) -> ProjectSignals:
    base = dict(
        requirements_stable=False,
        hard_deadline=False,
        many_dependencies=False,
        continuous_flow=False,
        resource_constrained=False,
    )
    base.update(over)
    return ProjectSignals(**base)


def test_ccpm_for_constrained_dependency_deadline():
    rec = recommend_methodology(
        _signals(resource_constrained=True, many_dependencies=True, hard_deadline=True)
    )
    assert rec.methodology == Methodology.CCPM
    assert "project_buffer_pct" in rec.config


def test_cpm_for_dependencies_and_deadline():
    rec = recommend_methodology(_signals(many_dependencies=True, hard_deadline=True))
    assert rec.methodology == Methodology.CPM


def test_waterfall_for_stable_bounded():
    rec = recommend_methodology(_signals(requirements_stable=True, continuous_flow=False))
    assert rec.methodology == Methodology.WATERFALL


def test_kanban_for_continuous_flow():
    rec = recommend_methodology(_signals(continuous_flow=True))
    assert rec.methodology == Methodology.KANBAN
    assert "wip_limits" in rec.config


def test_scrum_for_evolving_requirements():
    rec = recommend_methodology(_signals(requirements_stable=False, continuous_flow=False))
    assert rec.methodology == Methodology.SCRUM


def test_rationale_present():
    rec = recommend_methodology(_signals(continuous_flow=True))
    assert rec.rationale
