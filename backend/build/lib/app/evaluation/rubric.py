"""Deterministic evaluation rubric.

A rubric is a list of criterion specs evaluated against an execution's output by
pure, side-effect-free validators. This is the deterministic-validation path; an
evaluator agent (evaluation_service) can layer a narrative critique on top, but
the gate here is reproducible and exhaustively testable.

Criterion spec shape (JSON-friendly):
    {"key": "has_summary", "check": "min_length", "weight": 1.0, "params": {"min": 50}}
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.core.enums import Verdict


@dataclass(frozen=True)
class CriterionResult:
    key: str
    weight: float
    passed: bool
    score: float
    notes: str


@dataclass(frozen=True)
class RubricOutcome:
    verdict: Verdict
    score: float
    criteria: list[CriterionResult]
    gaps: list[str]


def _check(check: str, output: str, params: dict) -> tuple[bool, str]:
    text = output or ""
    if check == "non_empty":
        ok = bool(text.strip())
        return ok, "" if ok else "output is empty"
    if check == "min_length":
        n = int(params.get("min", 1))
        ok = len(text) >= n
        return ok, "" if ok else f"length {len(text)} < required {n}"
    if check == "max_length":
        n = int(params.get("max", 10_000))
        ok = len(text) <= n
        return ok, "" if ok else f"length {len(text)} > allowed {n}"
    if check == "contains_all":
        kws = params.get("keywords", [])
        missing = [k for k in kws if k.lower() not in text.lower()]
        return (not missing), "" if not missing else f"missing keywords: {missing}"
    if check == "contains_any":
        kws = params.get("keywords", [])
        ok = any(k.lower() in text.lower() for k in kws)
        return ok, "" if ok else f"none of the keywords present: {kws}"
    if check == "is_json":
        try:
            json.loads(text)
            return True, ""
        except (ValueError, TypeError):
            return False, "output is not valid JSON"
    if check == "regex":
        pattern = params.get("pattern", "")
        ok = bool(re.search(pattern, text))
        return ok, "" if ok else f"pattern not found: {pattern}"
    # Unknown check fails closed.
    return False, f"unknown check: {check}"


def evaluate_deterministic(output: str, specs: list[dict]) -> RubricOutcome:
    """Evaluate ``output`` against criterion specs. Empty specs => trivially passes."""
    if not specs:
        return RubricOutcome(Verdict.PASS, 1.0, [], [])

    results: list[CriterionResult] = []
    for spec in specs:
        key = spec.get("key", spec.get("check", "criterion"))
        weight = float(spec.get("weight", 1.0))
        passed, notes = _check(spec.get("check", ""), output, spec.get("params", {}))
        results.append(
            CriterionResult(
                key=key, weight=weight, passed=passed, score=1.0 if passed else 0.0, notes=notes
            )
        )

    total_weight = sum(r.weight for r in results) or 1.0
    score = sum(r.weight * r.score for r in results) / total_weight
    gaps = [f"{r.key}: {r.notes}" for r in results if not r.passed]

    if all(r.passed for r in results):
        verdict = Verdict.PASS
    elif score >= 0.5:
        verdict = Verdict.NEEDS_REVISION
    else:
        verdict = Verdict.FAIL

    return RubricOutcome(verdict=verdict, score=score, criteria=results, gaps=gaps)
