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
- ``[[REMEDIATE_ONCE:<token>]]`` -> omits the token until the runtime supplies
  evaluation-gap feedback, then includes it in the remediated answer.
- ``[[AUTONOMOUS_DEMO:DEMO_ACCEPTED]]`` -> returns the governed two-task demo
  plan when the provider is called with the plan contract.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re

from app.orchestration.ports import AgentRunRequest, AgentRunResult, ToolCall

_SLEEP_RE = re.compile(r"\[\[SLEEP:([0-9]+(?:\.[0-9]+)?)\]\]")
_REVIEWED_OUTPUT_RE = re.compile(r"--- OUTPUT ---\n(.*)\n--- END ---", re.DOTALL)
_TOOL_START_RE = re.compile(r"\[\[TOOL:([\w.\-]+):")
_TOOL_LOOP_RE = re.compile(r"\[\[TOOL_LOOP:([\w.\-]+)\]\]")
_REMEDIATE_ONCE_RE = re.compile(r"\[\[REMEDIATE_ONCE:([\w.\-]+)\]\]")
_TOOL_RESULTS_RE = re.compile(
    r"\[\[TOOL_RESULTS\]\]\n(.*?)\nUse these tool results",
    re.DOTALL,
)


def _tool_calls(prompt: str) -> list[ToolCall]:
    """Parse tool markers with nested JSON objects without relaxing the marker contract."""
    calls: list[ToolCall] = []
    decoder = json.JSONDecoder()
    for match in _TOOL_START_RE.finditer(prompt):
        try:
            arguments, end = decoder.raw_decode(prompt, match.end())
        except json.JSONDecodeError as exc:
            raise ValueError("tool marker arguments are not valid JSON") from exc
        if not isinstance(arguments, dict) or not prompt.startswith("]]", end):
            raise ValueError("tool marker must contain one JSON object")
        calls.append(ToolCall(name=match.group(1), arguments=arguments))
    return calls


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
            calls = _tool_calls(prompt)
            if calls:
                return AgentRunResult(output="", tool_calls=calls, provider=self.name)

        digest = hashlib.sha256(f"{request.system or ''}\n{prompt}".encode()).hexdigest()
        if request.params.get("expected_format") == "verdict_json_v1":
            output = self._structured_verdict(prompt)
        elif request.params.get("expected_format") == "plan_json_v1":
            output = self._structured_plan(prompt)
        elif "[[AUTONOMOUS_ANALYSIS]]" in prompt:
            output = self._autonomous_analysis_output(prompt)
        else:
            output = f"[mock:{request.model or 'default'}] response::{digest[:16]}"
            remediation_tokens = _REMEDIATE_ONCE_RE.findall(prompt)
            if remediation_tokens and "Address these evaluation gaps:" in prompt:
                output += "\nResolved acceptance tokens: " + " ".join(remediation_tokens)
            else:
                for token in remediation_tokens:
                    output = re.sub(re.escape(token), "[pending]", output, flags=re.IGNORECASE)
        tokens = max(1, len(prompt) // 4)
        return AgentRunResult(
            output=output,
            tokens_used=tokens,
            cost_estimate=round(tokens * 1e-6, 8),
            provider=self.name,
            raw_id=digest[:32],
        )

    @staticmethod
    def _autonomous_analysis_output(prompt: str) -> str:
        """Report the real permissioned tool result, failing visibly if absent."""
        match = _TOOL_RESULTS_RE.search(prompt)
        if match is None:
            return "Permissioned analysis result unavailable."
        try:
            events = json.loads(match.group(1))
            event = events[0]
            stats = event["result"]["stats"]
            if event.get("status") != "ok":
                raise ValueError("tool status is not ok")
            return (
                "Permissioned regional analysis complete: "
                f"mean={stats['mean']}; sum={stats['sum']}; "
                f"min={stats['min']}; max={stats['max']}."
            )
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
            return "Permissioned analysis result unavailable."

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

    @staticmethod
    def _structured_plan(prompt: str) -> str:
        """Deterministic two-step plan for hermetic decomposition tests."""
        if "[[MALFORMED_PLAN]]" in prompt:
            return "This objective needs a research task and a delivery task."
        if "[[AUTONOMOUS_DEMO:DEMO_ACCEPTED]]" in prompt:
            return json.dumps(
                {
                    "tasks": [
                        {
                            "key": "research",
                            "title": "Research market demand",
                            "description": (
                                "Analyze the demand sample with the permissioned statistics tool. "
                                "[[AUTONOMOUS_ANALYSIS]] "
                                '[[TOOL:analysis.summary_stats:{"records":[{"value":120},'
                                '{"value":95},{"value":140},{"value":110}],'
                                '"value_column":"value"}]]'
                            ),
                            "estimate_hours": 1,
                            "required_capabilities": ["analysis.data"],
                            "priority": 2,
                            "acceptance_criteria": [
                                {"key": "research_output", "check": "non_empty"},
                                {
                                    "key": "real_mean",
                                    "check": "contains_all",
                                    "params": {"keywords": ["mean=116.25"]},
                                },
                            ],
                        },
                        {
                            "key": "deliver",
                            "title": "Deliver the market brief and demand chart",
                            "description": (
                                "Use the research findings to deliver the market brief and demand "
                                "chart. [[REMEDIATE_ONCE:DEMO_ACCEPTED]]"
                            ),
                            "estimate_hours": 1,
                            "required_capabilities": ["writing.brief"],
                            "priority": 1,
                            "acceptance_criteria": [
                                {"key": "deliverable_output", "check": "non_empty"},
                                {
                                    "key": "demo_accepted",
                                    "check": "contains_all",
                                    "params": {"keywords": ["DEMO_ACCEPTED"]},
                                },
                            ],
                        },
                    ],
                    "dependencies": [{"predecessor_key": "research", "successor_key": "deliver"}],
                    "project_acceptance": {
                        "criteria": [
                            {
                                "key": "demo_accepted",
                                "check": "contains_all",
                                "params": {"keywords": ["DEMO_ACCEPTED"]},
                            }
                        ],
                        "deliverables": ["market brief", "demand chart"],
                    },
                    "assumptions": [
                        "An executor and evaluator will be assigned before project start."
                    ],
                    "warnings": [],
                }
            )
        return json.dumps(
            {
                "tasks": [
                    {
                        "key": "research",
                        "title": "Research the objective",
                        "description": "Gather and analyze the evidence needed for the objective.",
                        "estimate_hours": 1,
                        "required_capabilities": [],
                        "priority": 2,
                        "acceptance_criteria": [{"key": "research_output", "check": "non_empty"}],
                    },
                    {
                        "key": "deliver",
                        "title": "Deliver the objective",
                        "description": (
                            "Use the predecessor findings to produce the final deliverable."
                        ),
                        "estimate_hours": 1,
                        "required_capabilities": [],
                        "priority": 1,
                        "acceptance_criteria": [{"key": "delivery_output", "check": "non_empty"}],
                    },
                ],
                "dependencies": [{"predecessor_key": "research", "successor_key": "deliver"}],
                "project_acceptance": {
                    "criteria": [{"key": "project_output", "check": "non_empty"}],
                    "deliverables": [],
                },
                "assumptions": ["An executor agent will be assigned before project start."],
                "warnings": [],
            }
        )
