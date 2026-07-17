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


async def test_mock_provider_is_deterministic():
    provider = MockProvider()
    req = AgentRunRequest(prompt="hello world", model="x")
    r1 = await provider.run(req)
    r2 = await provider.run(req)
    assert r1.output == r2.output
    assert r1.provider == "mock"
    assert r1.tokens_used > 0


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
