"""Remediation policy selection."""

from __future__ import annotations

from app.core.enums import RemediationAction, Verdict
from app.remediation.policy import RemediationContext, select_remediation


def test_budget_exhausted_escalates():
    ctx = RemediationContext(Verdict.FAIL, 0.1, ["x"], remediations_used=1, max_remediations=1)
    d = select_remediation(ctx)
    assert d.action == RemediationAction.ESCALATE_HUMAN
    assert not d.auto_applicable


def test_missing_tool_gap_selects_add_tool():
    ctx = RemediationContext(Verdict.FAIL, 0.4, ["needs a search tool"], max_remediations=2)
    assert select_remediation(ctx).action == RemediationAction.ADD_TOOL


def test_needs_revision_adds_context():
    ctx = RemediationContext(Verdict.NEEDS_REVISION, 0.6, ["too short"], max_remediations=2)
    d = select_remediation(ctx)
    assert d.action == RemediationAction.ADD_CONTEXT
    assert d.auto_applicable


def test_low_score_with_alternate_replaces_agent():
    ctx = RemediationContext(
        Verdict.FAIL, 0.1, ["bad output"], max_remediations=2, has_alternate_agent=True
    )
    assert select_remediation(ctx).action == RemediationAction.REPLACE_AGENT


def test_default_is_reprompt():
    ctx = RemediationContext(Verdict.FAIL, 0.4, ["weak"], max_remediations=2)
    d = select_remediation(ctx)
    assert d.action == RemediationAction.RE_PROMPT
    assert d.auto_applicable
