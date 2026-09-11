"""Capability taxonomy.

A curated, dotted-namespace vocabulary of capabilities an agent can declare and
a task can require. Matching (app/services/matching.py) compares required vs.
declared capabilities against this shared vocabulary. New keys are added here so
the taxonomy stays governed rather than free-form.
"""

from __future__ import annotations

#: category -> capability keys
TAXONOMY: dict[str, tuple[str, ...]] = {
    "research": ("research.web", "research.literature", "research.market"),
    "analysis": ("analysis.python", "analysis.r", "analysis.data", "analysis.stats"),
    "writing": ("writing.brief", "writing.report", "writing.summary", "writing.copy"),
    "viz": ("viz.chart", "viz.dashboard", "viz.diagram"),
    "coding": ("coding.python", "coding.review", "coding.sql"),
    "planning": ("planning.decompose", "planning.estimate"),
    "evaluation": ("evaluation.rubric", "evaluation.factcheck"),
}

KNOWN_CAPABILITIES: frozenset[str] = frozenset(key for keys in TAXONOMY.values() for key in keys)


def is_known_capability(key: str) -> bool:
    return key in KNOWN_CAPABILITIES


def unknown_capabilities(keys: list[str]) -> list[str]:
    """Return the subset of ``keys`` not present in the taxonomy."""
    return [k for k in keys if k not in KNOWN_CAPABILITIES]
