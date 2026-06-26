"""Evaluator-agent verdict combination (issue 0004)."""

from __future__ import annotations

from app.core.enums import Verdict
from app.services.evaluation_service import agent_structured_verdict, combine_verdicts


def test_agent_can_downgrade_pass():
    assert combine_verdicts(Verdict.PASS, Verdict.NEEDS_REVISION) == Verdict.NEEDS_REVISION
    assert combine_verdicts(Verdict.PASS, Verdict.FAIL) == Verdict.FAIL


def test_agent_cannot_upgrade_hard_fail():
    assert combine_verdicts(Verdict.FAIL, Verdict.PASS) == Verdict.FAIL
    assert combine_verdicts(Verdict.NEEDS_REVISION, Verdict.PASS) == Verdict.NEEDS_REVISION


def test_agreement_passes_through():
    assert combine_verdicts(Verdict.PASS, Verdict.PASS) == Verdict.PASS


def test_structured_verdict_heuristic():
    assert agent_structured_verdict("")[0] == Verdict.FAIL
    assert agent_structured_verdict("short")[0] == Verdict.NEEDS_REVISION
    assert agent_structured_verdict("a sufficiently long output here")[0] == Verdict.PASS
