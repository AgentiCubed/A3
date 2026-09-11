"""Provider preflight: cheap credential/endpoint checks without project work."""

from __future__ import annotations

import httpx

from app.orchestration.adapters.anthropic_provider import AnthropicProvider
from app.orchestration.adapters.openai_compatible_provider import OpenAICompatibleProvider
from app.orchestration.ports import AgentRunResult, ProviderErrorCategory
from app.services.provider_preflight import preflight_provider


async def test_mock_preflight_always_passes():
    result = await preflight_provider("mock")
    assert result.ok is True
    assert result.provider == "mock"
    assert result.diagnostic is None


async def test_retired_provider_preflight_fails_with_guidance():
    result = await preflight_provider("github_models")
    assert result.ok is False
    assert result.category == ProviderErrorCategory.NOT_FOUND.value
    assert result.http_status == 410
    assert "retired" in result.message
    assert "gemini" in result.message
    assert result.diagnostic is not None
    assert "provider_error_category=not_found" in result.diagnostic


async def test_unknown_provider_preflight_fails_closed():
    result = await preflight_provider("does-not-exist")
    assert result.ok is False
    assert result.category == ProviderErrorCategory.NOT_FOUND.value
    assert "unknown provider" in result.message


async def test_missing_credential_preflight_is_authentication(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = await preflight_provider("gemini")
    assert result.ok is False
    assert result.category == ProviderErrorCategory.AUTHENTICATION.value
    assert "Credential missing or malformed" in result.message
    assert result.diagnostic == ("provider_http_status=none provider_error_category=authentication")


async def test_live_preflight_ping_succeeds_with_stub_transport(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "preflight-1",
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 1},
            },
        )

    stub = OpenAICompatibleProvider(
        name="gemini",
        base_url="https://compat.example.invalid/v1",
        default_model="gemini-2.5-flash",
        default_credential_ref="GEMINI_API_KEY",
        transport=httpx.MockTransport(_handler),
    )
    monkeypatch.setattr(
        "app.services.provider_preflight.get_adapter",
        lambda _name: stub,
    )
    result = await preflight_provider("gemini", model="gemini-2.5-flash")
    assert result.ok is True
    assert "successfully" in result.message.lower()


async def test_live_preflight_maps_http_failure(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "no such model"})

    stub = OpenAICompatibleProvider(
        name="gemini",
        base_url="https://compat.example.invalid/v1",
        default_model="nope",
        default_credential_ref="GEMINI_API_KEY",
        transport=httpx.MockTransport(_handler),
        # Exhaust retries immediately so the test stays fast.
        transient_retry_delays=[],
        rate_limit_retry_delays=[],
    )
    monkeypatch.setattr(
        "app.services.provider_preflight.get_adapter",
        lambda _name: stub,
    )
    result = await preflight_provider("gemini")
    assert result.ok is False
    assert result.category == ProviderErrorCategory.NOT_FOUND.value
    assert result.http_status == 404
    assert "Model or endpoint not found" in result.message


async def test_anthropic_preflight_reports_default_model(monkeypatch):
    adapter = AnthropicProvider()

    async def _run(_request):
        return AgentRunResult(output="ok", provider="anthropic")

    monkeypatch.setattr(adapter, "run", _run)
    monkeypatch.setattr(
        "app.services.provider_preflight.get_adapter",
        lambda _name: adapter,
    )

    result = await preflight_provider("anthropic")
    assert result.ok is True
    assert result.model == "claude-sonnet-4-6"
