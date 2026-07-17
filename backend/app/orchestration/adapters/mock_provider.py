"""Deterministic mock provider for tests and offline development.

Produces stable, reproducible output for a given request (no network, no
randomness), so deterministic tests never call a live provider (assumption A15).
Token/cost figures are derived deterministically from input length.

Control markers (dual-use: failure-path tests AND the Phase-8 deliberate failure):
- ``[[FAIL]]`` anywhere in the prompt -> raises, simulating an execution error.
- ``[[SLEEP:<seconds>]]`` -> awaits that many seconds (drives timeout tests).
- ``[[TOOL:<name>:<json args>]]`` -> answers with that tool call until tool
  results appear in the prompt (``[[TOOL_RESULTS]]``), then answers normally.
- ``[[TOOL_LOOP:<name>]]`` -> ALWAYS answers with a tool call, never a final
  answer — drives the runtime's budget-termination tests.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re

from app.orchestration.ports import AgentRunRequest, AgentRunResult, ToolCall

_SLEEP_RE = re.compile(r"\[\[SLEEP:([0-9]+(?:\.[0-9]+)?)\]\]")
_REVIEWED_OUTPUT_RE = re.compile(r"--- OUTPUT ---\n(.*)\n--- END ---", re.DOTALL)
_TOOL_RE = re.compile(r"\[\[TOOL:([\w.\-]+):(\{.*?\})\]\]", re.DOTALL)
_TOOL_LOOP_RE = re.compile(r"\[\[TOOL_LOOP:([\w.\-]+)\]\]")


class MockProviderError(RuntimeError):
    """Raised by MockProvider when the prompt contains the [[FAIL]] marker."""


class MockProvider:
    name = "mock"

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        prompt = request.prompt

        sleep_match = _SLEEP_RE.search(prompt)
        if sleep_match:
            await asyncio.sleep(float(sleep_match.group(1)))

        if "[[FAIL]]" in prompt:
            raise MockProviderError("simulated execution failure")

        loop_match = _TOOL_LOOP_RE.search(prompt)
        if loop_match:
            return AgentRunResult(
                output="",
                tool_calls=[ToolCall(name=loop_match.group(1), arguments={})],
                provider=self.name,
            )
        if "[[TOOL_RESULTS]]" not in prompt:
            calls = [
                ToolCall(name=m.group(1), arguments=json.loads(m.group(2)))
                for m in _TOOL_RE.finditer(prompt)
            ]
            if calls:
                return AgentRunResult(output="", tool_calls=calls, provider=self.name)

        digest = hashlib.sha256(f"{request.system or ''}\n{prompt}".encode()).hexdigest()
        if request.params.get("expected_format") == "verdict_json_v1":
            output = self._structured_verdict(prompt)
        else:
            output = f"[mock:{request.model or 'default'}] response::{digest[:16]}"
        tokens = max(1, len(prompt) // 4)
        return AgentRunResult(
            output=output,
            tokens_used=tokens,
            cost_estimate=round(tokens * 1e-6, 8),
            provider=self.name,
            raw_id=digest[:32],
        )

    @staticmethod
    def _structured_verdict(prompt: str) -> str:
        """Deterministic evaluator answer honoring the verdict_json_v1 contract.

        Judges the text between the review markers with a fixed rule (empty →
        fail, very short → needs_revision, else pass) so evaluation tests stay
        reproducible without a live model. ``[[MALFORMED]]`` in the reviewed
        output forces a contract-violating prose reply, for fail-closed tests.
        """
        match = _REVIEWED_OUTPUT_RE.search(prompt)
        reviewed = (match.group(1) if match else "").strip()
        if "[[MALFORMED]]" in reviewed:
            return "Looks great overall, ship it!"
        if not reviewed:
            verdict, score, critique = "fail", 0.0, "reviewed output is empty"
        elif len(reviewed) < 16:
            verdict, score, critique = "needs_revision", 0.5, "reviewed output is very short"
        else:
            verdict, score, critique = "pass", 1.0, "reviewed output looks complete"
        return json.dumps({"verdict": verdict, "score": score, "critique": critique, "gaps": []})
