"""Closed-loop remediation policy.

Given a failed/needs-revision evaluation, selects ONE of the ten remediation
actions and returns a justification. Pure and rule-based (deterministic, testable);
upgradeable to model-assisted later. The orchestrator records the selected action
and justification, then either auto-applies it (re-execute) or escalates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import RemediationAction, Verdict

#: Actions the orchestrator can apply automatically by re-executing inline.
#: The rest require human/planning/registry changes and therefore escalate.
AUTO_APPLICABLE: frozenset[RemediationAction] = frozenset(
    {RemediationAction.RE_PROMPT, RemediationAction.ADD_CONTEXT}
)


@dataclass(frozen=True)
class RemediationContext:
    verdict: Verdict
    score: float
    gaps: list[str] = field(default_factory=list)
    remediations_used: int = 0
    max_remediations: int = 1
    has_alternate_agent: bool = False


@dataclass(frozen=True)
class RemediationDecision:
    action: RemediationAction
    justification: str

    @property
    def auto_applicable(self) -> bool:
        return self.action in AUTO_APPLICABLE


def select_remediation(ctx: RemediationContext) -> RemediationDecision:
    """Pick a remediation action from the evaluation signal. First match wins."""
    if ctx.remediations_used >= ctx.max_remediations:
        return RemediationDecision(
            RemediationAction.ESCALATE_HUMAN,
            "remediation budget exhausted; escalating to a human approver",
        )

    gaps_text = " ".join(ctx.gaps).lower()

    if "tool" in gaps_text or "source" in gaps_text:
        return RemediationDecision(
            RemediationAction.ADD_TOOL,
            "gap indicates a missing tool or data source the agent lacked",
        )
    if "json" in gaps_text or "format" in gaps_text:
        return RemediationDecision(
            RemediationAction.ADD_CONTEXT,
            "output-format gap; re-prompt with explicit format guidance",
        )
    if ctx.verdict == Verdict.NEEDS_REVISION:
        return RemediationDecision(
            RemediationAction.ADD_CONTEXT,
            "minor gaps; re-prompt the same agent with targeted feedback",
        )
    if ctx.score < 0.25 and ctx.has_alternate_agent:
        return RemediationDecision(
            RemediationAction.REPLACE_AGENT,
            "very low score with an alternate agent available; replace the agent",
        )
    return RemediationDecision(
        RemediationAction.RE_PROMPT,
        "re-prompt the same agent with the evaluation gaps as feedback",
    )
