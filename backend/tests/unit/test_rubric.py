"""Deterministic rubric evaluation."""

from __future__ import annotations

from app.core.enums import Verdict
from app.evaluation.rubric import evaluate_deterministic


def test_empty_rubric_passes():
    out = evaluate_deterministic("anything", [])
    assert out.verdict == Verdict.PASS
    assert out.score == 1.0


def test_all_pass():
    specs = [
        {"key": "nonempty", "check": "non_empty", "weight": 1},
        {"key": "len", "check": "min_length", "weight": 1, "params": {"min": 3}},
    ]
    out = evaluate_deterministic("hello world", specs)
    assert out.verdict == Verdict.PASS
    assert out.gaps == []


def test_total_fail():
    specs = [
        {"key": "kw", "check": "contains_all", "weight": 1, "params": {"keywords": ["ZZZ"]}},
        {"key": "len", "check": "min_length", "weight": 1, "params": {"min": 1000}},
    ]
    out = evaluate_deterministic("short", specs)
    assert out.verdict == Verdict.FAIL
    assert len(out.gaps) == 2


def test_partial_is_needs_revision():
    specs = [
        {"key": "nonempty", "check": "non_empty", "weight": 1},  # passes
        {
            "key": "kw",
            "check": "contains_all",
            "weight": 1,
            "params": {"keywords": ["ZZZ"]},
        },  # fails
    ]
    out = evaluate_deterministic("present", specs)
    assert out.verdict == Verdict.NEEDS_REVISION
    assert 0 < out.score < 1


def test_is_json_check():
    assert evaluate_deterministic('{"a": 1}', [{"check": "is_json"}]).verdict == Verdict.PASS
    assert evaluate_deterministic("not json", [{"check": "is_json"}]).verdict == Verdict.FAIL
