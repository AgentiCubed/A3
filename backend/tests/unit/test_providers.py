"""Provider adapters and the registry."""

from __future__ import annotations

import json

import httpx
import pytest

from app.core.secrets import CredentialNotConfigured
from app.orchestration.adapters.anthropic_provider import AnthropicProvider, _estimate_cost
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.adapters.openai_compatible_provider import (
    OpenAICompatibleProvider,
    RetiredProvider,
)
from app.orchestration.adapters.registry import (
    UnknownProvider,
    available_providers,
    get_adapter,
    retirement_guidance,
)
from app.orchestration.ports import (
    AgentRunRequest,
    ProviderCallError,
    ProviderErrorCategory,
    parse_provider_diagnostic,
)
from app.services.decomposition_service import parse_plan

_COMPAT_BASE_URL = "https://compat.example.invalid/v1"


def _compat(**kwargs) -> OpenAICompatibleProvider:
    """A gemini-shaped OpenAI-compatible adapter pointed at a stub host."""
    return OpenAICompatibleProvider(
        name="gemini",
        base_url=_COMPAT_BASE_URL,
        default_model="gemini-2.5-flash",
        default_credential_ref="GEMINI_API_KEY",
        **kwargs,
    )


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
    assert get_adapter("gemini").name == "gemini"
    assert get_adapter("ollama").name == "ollama"
    assert "anthropic" in available_providers()
    assert "gemini" in available_providers()
    assert "ollama" in available_providers()
    # The retired provider still resolves (stored agents must fail readably)
    # but is not selectable for new work.
    assert isinstance(get_adapter("github_models"), RetiredProvider)
    assert "github_models" not in available_providers()
    with pytest.raises(UnknownProvider):
        get_adapter("does-not-exist")


async def test_anthropic_resolves_credential_before_network(monkeypatch):
    # With no API key in the environment, the adapter must fail fast (no network).
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = AnthropicProvider()
    with pytest.raises(CredentialNotConfigured):
        await provider.run(AgentRunRequest(prompt="hi"))


async def test_openai_compatible_resolves_credential_before_network(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = _compat()
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="hi"))
    assert str(caught.value) == ("provider_http_status=none provider_error_category=authentication")


async def test_openai_compatible_redacts_missing_credential_reference(monkeypatch):
    credential_ref = "secret-credential-reference-sentinel"
    monkeypatch.delenv(credential_ref, raising=False)
    provider = _compat()
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="hi", credential_ref=credential_ref))

    assert str(caught.value) == ("provider_http_status=none provider_error_category=authentication")
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert credential_ref not in repr(caught.value)


async def test_openai_compatible_redacts_malformed_credential_reference():
    provider = _compat()
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(
            AgentRunRequest(
                prompt="secret-prompt-sentinel",
                credential_ref=123,  # type: ignore[arg-type]
            )
        )

    assert str(caught.value) == (
        "provider_http_status=none provider_error_category=invalid_request"
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)


async def test_openai_compatible_redacts_invalid_request_inputs(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-token-sentinel")
    provider = _compat()
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(
            AgentRunRequest(
                prompt="secret-prompt-sentinel",
                params={"max_tokens": "secret-invalid-token-count"},
            )
        )

    assert str(caught.value) == (
        "provider_http_status=none provider_error_category=invalid_request"
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)


async def test_openai_compatible_maps_live_response_without_persisting_token(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-token"
        payload = json.loads(request.content)
        assert payload["model"] == "gemini-2.5-flash"
        assert payload["messages"] == [{"role": "user", "content": "Say hello"}]
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-receipt",
                "choices": [{"message": {"role": "assistant", "content": "hello"}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
            },
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    result = await provider.run(AgentRunRequest(prompt="Say hello"))
    assert result.output == "hello"
    assert result.provider == "gemini"
    assert result.tokens_used == 6
    assert result.raw_id == "chatcmpl-receipt"
    assert "test-token" not in repr(result)


async def test_openai_compatible_tolerates_response_without_id_or_usage(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "hello"}}]},
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    result = await provider.run(AgentRunRequest(prompt="Say hello"))
    assert result.tokens_used == 0
    assert result.raw_id is None


@pytest.mark.parametrize(
    ("status_code", "category"),
    [
        (400, ProviderErrorCategory.INVALID_REQUEST),
        (401, ProviderErrorCategory.AUTHENTICATION),
        (403, ProviderErrorCategory.AUTHORIZATION),
        (404, ProviderErrorCategory.NOT_FOUND),
        (408, ProviderErrorCategory.TIMEOUT),
        (409, ProviderErrorCategory.INVALID_REQUEST),
        (429, ProviderErrorCategory.RATE_LIMITED),
        (500, ProviderErrorCategory.PROVIDER_UNAVAILABLE),
        (504, ProviderErrorCategory.TIMEOUT),
    ],
)
async def test_openai_compatible_maps_http_errors_to_safe_diagnostics(
    monkeypatch, status_code, category
):
    token = "secret-token-sentinel"
    prompt = "secret-prompt-sentinel"
    monkeypatch.setenv("GEMINI_API_KEY", token)

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            headers={"x-secret-sentinel": "secret-header-sentinel"},
            json={"error": "secret-body-sentinel"},
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt=prompt))

    expected = f"provider_http_status={status_code} " f"provider_error_category={category.value}"
    assert str(caught.value) == expected
    assert caught.value.args == (expected,)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert not hasattr(caught.value, "request")
    assert not hasattr(caught.value, "response")
    rendered = repr(caught.value)
    for secret in (
        token,
        prompt,
        "secret-header-sentinel",
        "secret-body-sentinel",
        "compat.example.invalid",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    ("transport_error", "category"),
    [
        (httpx.ReadTimeout, ProviderErrorCategory.TIMEOUT),
        (httpx.ConnectError, ProviderErrorCategory.NETWORK_ERROR),
    ],
)
async def test_openai_compatible_redacts_transport_errors(monkeypatch, transport_error, category):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-token-sentinel")

    def _handler(request: httpx.Request) -> httpx.Response:
        raise transport_error("secret-network-sentinel", request=request)

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="secret-prompt-sentinel"))

    expected = f"provider_http_status=none provider_error_category={category.value}"
    assert str(caught.value) == expected
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)


async def test_openai_compatible_redacts_invalid_success_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-token-sentinel")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="secret-invalid-json-sentinel")

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="secret-prompt-sentinel"))

    assert str(caught.value) == (
        "provider_http_status=200 provider_error_category=provider_unavailable"
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)


async def test_openai_compatible_redacts_unexpected_response_parse_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-token-sentinel")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=(
                b'{"choices":[{"message":{"content":"secret-output-sentinel"}}],'
                b'"usage":{"total_tokens":1e999}}'
            ),
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="secret-prompt-sentinel"))

    assert str(caught.value) == (
        "provider_http_status=200 provider_error_category=provider_unavailable"
    )
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)


def test_provider_diagnostic_parser_fails_closed():
    assert parse_provider_diagnostic(
        "provider_http_status=403 provider_error_category=authorization"
    ) == (403, "authorization")
    assert parse_provider_diagnostic(
        "provider_http_status=none provider_error_category=network_error"
    ) == (None, "network_error")
    assert parse_provider_diagnostic(
        "provider_http_status=403 provider_error_category=authorization secret=leak"
    ) == (None, None)
    assert parse_provider_diagnostic("HTTPStatusError: raw provider failure") == (None, None)


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


# ── Behaviour introduced by the 2026-08-02 provider migration ─────────────
# GitHub Models was retired on 2026-07-30 (410 Gone). These cover the
# properties that made that outage expensive to diagnose: an unreadable
# status mapping, an unconditional response_format, and a hard-deleted
# adapter that would have orphaned stored agents.


async def test_openai_compatible_sends_full_token_budget_and_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    seen: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        seen["_url"] = str(request.url)
        seen["_auth"] = request.headers.get("authorization")
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    await provider.run(AgentRunRequest(prompt="hi", model="gemini-2.5-pro"))

    assert seen["_url"] == f"{_COMPAT_BASE_URL}/chat/completions"
    assert seen["_auth"] == "Bearer test-token"
    assert seen["model"] == "gemini-2.5-pro"
    # A demo-scale floor (128) truncated real plans into unparseable JSON.
    assert seen["max_tokens"] == 2048


async def test_openai_compatible_uses_default_model_when_unset(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    seen: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    await provider.run(AgentRunRequest(prompt="hi"))
    assert seen["model"] == "gemini-2.5-flash"


async def test_openai_compatible_forwards_requested_response_format(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    seen: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "{}"}}]}
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    await provider.run(
        AgentRunRequest(
            prompt="plan",
            params={"response_format": {"type": "json_object"}, "max_tokens": 4096},
        )
    )
    assert seen["response_format"] == {"type": "json_object"}
    assert seen["max_tokens"] == 4096


async def test_openai_compatible_retries_once_without_unsupported_response_format(monkeypatch):
    """A model that rejects JSON mode must not fail the whole plan."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    attempts: list[dict] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        attempts.append(body)
        if "response_format" in body:
            return httpx.Response(400, json={"error": "response_format is not supported"})
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "plain"}}]}
        )

    provider = _compat(transport=httpx.MockTransport(_handler))
    result = await provider.run(
        AgentRunRequest(prompt="plan", params={"response_format": {"type": "json_object"}})
    )

    assert result.output == "plain"
    assert len(attempts) == 2
    assert "response_format" in attempts[0]
    assert "response_format" not in attempts[1]


async def test_openai_compatible_does_not_retry_when_no_response_format_requested(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    attempts: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        attempts.append(str(request.url))
        return httpx.Response(400, json={"error": "bad"})

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError):
        await provider.run(AgentRunRequest(prompt="hi"))
    assert len(attempts) == 1


async def test_openai_compatible_surfaces_retry_failure_status(monkeypatch):
    """When the retry also fails, the second status is what gets reported."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(400 if "response_format" in body else 429, json={})

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(
            AgentRunRequest(prompt="hi", params={"response_format": {"type": "json_object"}})
        )
    assert caught.value.http_status == 429
    assert caught.value.category is ProviderErrorCategory.RATE_LIMITED


async def test_openai_compatible_maps_410_gone_to_not_found(monkeypatch):
    """The GitHub Models retirement signal must read as 'gone', not 'bad request'."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")

    def _handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(410, json={"error": "gone"})

    provider = _compat(transport=httpx.MockTransport(_handler))
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="hi"))
    assert caught.value.http_status == 410
    assert caught.value.category is ProviderErrorCategory.NOT_FOUND
    assert str(caught.value) == "provider_http_status=410 provider_error_category=not_found"


async def test_local_provider_runs_without_a_credential(monkeypatch):
    """Ollama accepts unauthenticated local calls; absence of a key is not an error."""
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    seen: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "local"}}]}
        )

    provider = OpenAICompatibleProvider(
        name="ollama",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        default_credential_ref="OLLAMA_API_KEY",
        requires_credential=False,
        transport=httpx.MockTransport(_handler),
    )
    result = await provider.run(AgentRunRequest(prompt="hi"))
    assert result.output == "local"
    assert result.provider == "ollama"
    assert seen["auth"] is None


async def test_retired_provider_fails_with_a_typed_gone_error():
    """Stored agents on a retired provider fail readably, not with a crash."""
    provider = RetiredProvider(name="github_models", retired_on="2026-07-30", replacement="gemini")
    with pytest.raises(ProviderCallError) as caught:
        await provider.run(AgentRunRequest(prompt="hi"))
    assert caught.value.http_status == 410
    assert caught.value.category is ProviderErrorCategory.NOT_FOUND
    assert "2026-07-30" in provider.guidance
    assert "gemini" in provider.guidance


def test_retirement_guidance_is_available_for_operators():
    assert retirement_guidance("github_models") is not None
    assert "gemini" in retirement_guidance("github_models")
    assert retirement_guidance("gemini") is None
    assert retirement_guidance("mock") is None


async def test_gemini_style_model_prefix_is_applied_when_missing(monkeypatch):
    """Gemini 404s on a bare model name; accept both spellings."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-token")
    seen: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content)["model"])
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )

    provider = OpenAICompatibleProvider(
        name="gemini",
        base_url=_COMPAT_BASE_URL,
        default_model="gemini-flash-latest",
        default_credential_ref="GEMINI_API_KEY",
        model_prefix="models/",
        transport=httpx.MockTransport(_handler),
    )
    await provider.run(AgentRunRequest(prompt="hi", model="gemini-2.5-flash"))
    await provider.run(AgentRunRequest(prompt="hi", model="models/gemini-2.5-pro"))
    await provider.run(AgentRunRequest(prompt="hi"))

    # Bare name gets the namespace; an already-qualified name is untouched;
    # the default is qualified too.
    assert seen == [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-flash-latest",
    ]


async def test_model_prefix_is_opt_in_per_provider(monkeypatch):
    """Providers without a namespace (OpenAI, Ollama) must not be rewritten."""
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    seen: list[str] = []

    def _handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content)["model"])
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        )

    provider = OpenAICompatibleProvider(
        name="ollama",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        default_credential_ref="OLLAMA_API_KEY",
        requires_credential=False,
        transport=httpx.MockTransport(_handler),
    )
    await provider.run(AgentRunRequest(prompt="hi", model="llama3.2"))
    assert seen == ["llama3.2"]


def test_registered_gemini_qualifies_models():
    assert get_adapter("gemini")._qualified_model("gemini-2.5-flash") == ("models/gemini-2.5-flash")
    assert get_adapter("ollama")._qualified_model("llama3.2") == "llama3.2"
