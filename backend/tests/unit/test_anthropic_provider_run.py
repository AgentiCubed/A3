"""AnthropicProvider.run — request construction and response parsing.

No network is used: an ``httpx.MockTransport`` is injected into the adapter's
``AsyncClient`` so the real Messages API is never called. The credential
fast-fail and cost estimation are covered in ``test_providers.py``; this file
covers the HTTP request/response path (payload shaping, header auth, text-block
extraction, token accounting, and error propagation).
"""

from __future__ import annotations

import json

import httpx
import pytest

from app.orchestration.adapters import anthropic_provider
from app.orchestration.adapters.anthropic_provider import AnthropicProvider
from app.orchestration.ports import AgentRunRequest


def _mock_transport(monkeypatch, handler) -> None:
    """Force the adapter's AsyncClient to route through a MockTransport."""
    real_client = anthropic_provider.httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs.setdefault("transport", httpx.MockTransport(handler))
        return real_client(*args, **kwargs)

    monkeypatch.setattr(anthropic_provider.httpx, "AsyncClient", factory)


async def test_run_builds_payload_and_parses_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "msg_abc",
                "content": [
                    {"type": "text", "text": "Hello "},
                    {"type": "tool_use", "text": "ignored-non-text"},
                    {"type": "text", "text": "world"},
                ],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )

    _mock_transport(monkeypatch, handler)
    result = await AnthropicProvider().run(
        AgentRunRequest(
            prompt="hi",
            system="be terse",
            model="claude-sonnet-4-6",
            params={"max_tokens": 256, "temperature": 0.2},
        )
    )

    # Response parsing: only text blocks are concatenated.
    assert result.output == "Hello world"
    assert result.tokens_used == 15
    assert result.provider == "anthropic"
    assert result.raw_id == "msg_abc"
    assert result.cost_estimate > 0

    # Request construction.
    body = captured["body"]
    assert body["model"] == "claude-sonnet-4-6"
    assert body["max_tokens"] == 256
    assert body["system"] == "be terse"
    assert body["temperature"] == 0.2
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    assert captured["headers"]["x-api-key"] == "sk-test"
    assert captured["headers"]["anthropic-version"] == "2023-06-01"


async def test_run_uses_defaults_and_omits_optional_fields(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [], "usage": {}})

    _mock_transport(monkeypatch, handler)
    result = await AnthropicProvider().run(AgentRunRequest(prompt="hi"))

    assert result.output == ""
    assert result.tokens_used == 0
    assert result.raw_id is None

    body = captured["body"]
    assert body["model"] == "claude-sonnet-4-6"  # default model
    assert body["max_tokens"] == 1024  # default max_tokens
    assert "system" not in body  # omitted when unset
    assert "temperature" not in body  # omitted when unset


async def test_run_honors_explicit_credential_ref(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("MY_CUSTOM_KEY", "sk-custom")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["key"] = request.headers["x-api-key"]
        return httpx.Response(200, json={"content": [], "usage": {}})

    _mock_transport(monkeypatch, handler)
    await AnthropicProvider().run(AgentRunRequest(prompt="hi", credential_ref="MY_CUSTOM_KEY"))
    assert captured["key"] == "sk-custom"


async def test_run_propagates_http_errors(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server_error"})

    _mock_transport(monkeypatch, handler)
    with pytest.raises(httpx.HTTPStatusError):
        await AnthropicProvider().run(AgentRunRequest(prompt="hi"))
