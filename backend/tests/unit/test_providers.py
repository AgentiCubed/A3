"""Provider adapters and the registry."""

from __future__ import annotations

import pytest

from app.core.secrets import CredentialNotConfigured
from app.orchestration.adapters.anthropic_provider import AnthropicProvider, _estimate_cost
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.adapters.registry import (
    UnknownProvider,
    available_providers,
    get_adapter,
)
from app.orchestration.ports import AgentRunRequest
from app.services.decomposition_service import parse_plan


async def test_mock_provider_is_deterministic():
    provider = MockProvider()
    req = AgentRunRequest(prompt="hello world", model="x")
    r1 = await provider.run(req)
    r2 = await provider.run(req)
    assert r1.output == r2.output
    assert r1.provider == "mock"
    assert r1.tokens_used > 0


async def test_mock_provider_autonomous_demo_plan_is_executable():
    provider = MockProvider()
    result = await provider.run(
        AgentRunRequest(
            prompt="Objective: [[AUTONOMOUS_DEMO:DEMO_ACCEPTED]]",
            params={"expected_format": "plan_json_v1"},
        )
    )

    plan = parse_plan(result.output)
    assert [task.key for task in plan.tasks] == ["research", "deliver"]
    assert plan.dependencies[0].predecessor_key == "research"
    assert plan.dependencies[0].successor_key == "deliver"
    assert plan.project_acceptance.deliverables == ["market brief", "demand chart"]
    assert plan.project_acceptance.criteria[0].params == {"keywords": ["DEMO_ACCEPTED"]}

    research_call = await provider.run(AgentRunRequest(prompt=plan.tasks[0].description))
    assert len(research_call.tool_calls) == 1
    assert research_call.tool_calls[0].name == "analysis.summary_stats"
    assert research_call.tool_calls[0].arguments == {
        "records": [{"value": 120}, {"value": 95}, {"value": 140}, {"value": 110}],
        "value_column": "value",
    }

    tool_result = await provider.run(
        AgentRunRequest(
            prompt=(
                plan.tasks[0].description
                + '\n\n[[TOOL_RESULTS]]\n[{"tool":"analysis.summary_stats",'
                '"status":"ok","result":{"stats":{"mean":116.25,"sum":465.0,'
                '"min":95.0,"max":140.0}}}]\nUse these tool results to produce your final answer.'
            )
        )
    )
    assert "mean=116.25" in tool_result.output
    assert "sum=465.0" in tool_result.output


async def test_mock_provider_remediates_once_after_evaluation_feedback():
    provider = MockProvider()
    marker = "[[REMEDIATE_ONCE:DEMO_ACCEPTED]]"

    first = await provider.run(AgentRunRequest(prompt=f"Deliver the brief. {marker}"))
    assert "DEMO_ACCEPTED" not in first.output

    retry = await provider.run(
        AgentRunRequest(
            prompt=(
                f"Deliver the brief. {marker}\n\n"
                "Address these evaluation gaps: missing keywords: ['DEMO_ACCEPTED']"
            )
        )
    )
    assert "DEMO_ACCEPTED" in retry.output


async def test_mock_provider_rejects_malformed_tool_marker():
    with pytest.raises(ValueError, match="tool marker arguments"):
        await MockProvider().run(
            AgentRunRequest(prompt="[[TOOL:analysis.summary_stats:{not-json}]]")
        )


def test_registry_resolution():
    assert get_adapter(None).name == "mock"
    assert get_adapter("mock").name == "mock"
    assert get_adapter("anthropic").name == "anthropic"
    assert "anthropic" in available_providers()
    with pytest.raises(UnknownProvider):
        get_adapter("does-not-exist")


async def test_anthropic_resolves_credential_before_network(monkeypatch):
    # With no API key in the environment, the adapter must fail fast (no network).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicProvider()
    with pytest.raises(CredentialNotConfigured):
        await provider.run(AgentRunRequest(prompt="hi"))


def test_estimate_cost_known_model():
    # 1 000 000 input + 1 000 000 output tokens for claude-sonnet-4-6 → $18
    cost = _estimate_cost("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert abs(cost - 18.0) < 0.0001


def test_estimate_cost_unknown_model_falls_back():
    # Unknown model falls back to default sonnet-4-6 rates.
    cost_known = _estimate_cost("claude-sonnet-4-6", 100_000, 50_000)
    cost_unknown = _estimate_cost("claude-future-model", 100_000, 50_000)
    assert cost_known == cost_unknown


def test_estimate_cost_zero_tokens():
    assert _estimate_cost("claude-haiku-3-5", 0, 0) == 0.0
