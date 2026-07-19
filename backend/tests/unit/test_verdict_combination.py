"""Evaluator-agent verdict combination and contract parsing (issue 0004, WS-4)."""

from __future__ import annotations

from app.core.enums import Verdict
from app.services.evaluation_service import combine_verdicts, parse_evaluator_verdict


def test_agent_can_downgrade_pass():
    assert combine_verdicts(Verdict.PASS, Verdict.NEEDS_REVISION) == Verdict.NEEDS_REVISION
    assert combine_verdicts(Verdict.PASS, Verdict.FAIL) == Verdict.FAIL


def test_agent_cannot_upgrade_hard_fail():
    assert combine_verdicts(Verdict.FAIL, Verdict.PASS) == Verdict.FAIL
    assert combine_verdicts(Verdict.NEEDS_REVISION, Verdict.PASS) == Verdict.NEEDS_REVISION


def test_agreement_passes_through():
    assert combine_verdicts(Verdict.PASS, Verdict.PASS) == Verdict.PASS


def test_parse_well_formed_verdict():
    av = parse_evaluator_verdict(
        '{"verdict": "pass", "score": 0.9, "critique": "solid", "gaps": ["minor typo"]}'
    )
    assert av.verdict == Verdict.PASS
    assert av.score == 0.9
    assert av.critique == "solid"
    assert av.gaps == ["minor typo"]
    assert av.malformed is False


def test_parse_accepts_fenced_json():
    av = parse_evaluator_verdict('Here you go:\n```json\n{"verdict": "fail"}\n```')
    assert av.verdict == Verdict.FAIL
    assert av.malformed is False


def test_parse_minimal_object():
    av = parse_evaluator_verdict('{"verdict": "needs_revision"}')
    assert av.verdict == Verdict.NEEDS_REVISION
    assert av.score is None
    assert av.gaps == []
    assert av.malformed is False


def test_prose_fails_closed_never_pass():
    av = parse_evaluator_verdict("Looks great overall, ship it!")
    assert av.verdict == Verdict.NEEDS_REVISION
    assert av.malformed is True


def test_malformed_variants_fail_closed():
    cases = [
        "",  # empty
        "null",  # JSON but not an object
        '["pass"]',  # array
        '{"verdict": "excellent"}',  # unknown verdict value
        '{"verdict": "pass", "score": 2}',  # score out of range
        '{"verdict": "pass", "score": true}',  # boolean score
        '{"verdict": "pass", "critique": 5}',  # critique not a string
        '{"verdict": "pass", "gaps": "none"}',  # gaps not a list
        '{"verdict": "pass", "gaps": [1]}',  # gaps items not strings
        '{"verdict":',  # truncated JSON
    ]
    for raw in cases:
        av = parse_evaluator_verdict(raw)
        assert av.verdict == Verdict.NEEDS_REVISION, raw
        assert av.malformed is True, raw


def test_malformed_can_never_be_silently_upgraded():
    """Even combined with a deterministic PASS, a malformed response gates."""
    av = parse_evaluator_verdict("not json at all")
    assert combine_verdicts(Verdict.PASS, av.verdict) == Verdict.NEEDS_REVISION
