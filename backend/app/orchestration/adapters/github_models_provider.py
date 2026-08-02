"""GitHub Models provider adapter.

GitHub Models exposes an OpenAI-compatible inference endpoint and can be
authorized in GitHub Actions with the job's short-lived ``GITHUB_TOKEN``. The
application still receives only a credential *reference*; the token itself is
resolved at call time and is never persisted or returned.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.secrets import CredentialNotConfigured, resolve_credential
from app.orchestration.ports import (
    AgentRunRequest,
    AgentRunResult,
    ProviderCallError,
    ProviderErrorCategory,
    ToolCall,
)

_DEFAULT_MODEL = "openai/gpt-4.1"
_DEFAULT_CREDENTIAL_REF = "GITHUB_MODELS_TOKEN"
_API_URL = "https://models.github.ai/inference/chat/completions"
_API_VERSION = "2026-03-10"


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def _http_error_category(status_code: int) -> ProviderErrorCategory:
    if status_code == 401:
        return ProviderErrorCategory.AUTHENTICATION
    if status_code == 403:
        return ProviderErrorCategory.AUTHORIZATION
    if status_code == 404:
        return ProviderErrorCategory.NOT_FOUND
    if status_code in {408, 504}:
        return ProviderErrorCategory.TIMEOUT
    if status_code == 429:
        return ProviderErrorCategory.RATE_LIMITED
    if 400 <= status_code <= 499:
        return ProviderErrorCategory.INVALID_REQUEST
    return ProviderErrorCategory.PROVIDER_UNAVAILABLE


class GitHubModelsProvider:
    """Run provider-neutral requests through the GitHub Models API."""

    name = "github_models"

    def __init__(
        self,
        *,
        timeout_seconds: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._timeout = timeout_seconds
        self._transport = transport

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        credential_error: ProviderCallError | None = None
        try:
            token = resolve_credential(request.credential_ref or _DEFAULT_CREDENTIAL_REF)
        except CredentialNotConfigured:
            credential_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.AUTHENTICATION,
            )
        except Exception:  # noqa: BLE001 - malformed references must not escape
            credential_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.INVALID_REQUEST,
            )
        if credential_error is not None:
            raise credential_error
        model = request.model or _DEFAULT_MODEL
        request_error: ProviderCallError | None = None
        try:
            messages: list[dict[str, str]] = []
            if request.system:
                messages.append({"role": "system", "content": request.system})
            messages.append({"role": "user", "content": request.prompt})

            payload: dict[str, Any] = {
                "model": model,
                # 128 was a demo-scale floor that truncated real plans and
                # deliverables into unparseable fragments; 2048 is a usable
                # default and callers (planner/executor) request more.
                "max_tokens": int(request.params.get("max_tokens", 2048)),
                "messages": messages,
            }
            if "temperature" in request.params:
                payload["temperature"] = request.params["temperature"]
            # Let a caller demand a pure-JSON response (e.g. the planner's
            # strict plan_json_v1 contract) so the model cannot wrap it in
            # prose or markdown that then fails to parse.
            response_format = request.params.get("response_format")
            if response_format:
                payload["response_format"] = response_format
            if request.tools:
                payload["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.input_schema,
                        },
                    }
                    for tool in request.tools
                ]

            headers = {
                "accept": "application/vnd.github+json",
                "authorization": f"Bearer {token}",
                "content-type": "application/json",
                "x-github-api-version": _API_VERSION,
            }
        except Exception:  # noqa: BLE001 - request inputs must not escape in errors
            request_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.INVALID_REQUEST,
            )
        if request_error is not None:
            raise request_error
        async with httpx.AsyncClient(
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            provider_error: ProviderCallError | None = None
            try:
                response = await client.post(_API_URL, json=payload, headers=headers)
            except httpx.TimeoutException:
                provider_error = ProviderCallError(
                    http_status=None,
                    category=ProviderErrorCategory.TIMEOUT,
                )
            except httpx.RequestError:
                provider_error = ProviderCallError(
                    http_status=None,
                    category=ProviderErrorCategory.NETWORK_ERROR,
                )
            except Exception:  # noqa: BLE001 - request construction must not expose inputs
                provider_error = ProviderCallError(
                    http_status=None,
                    category=ProviderErrorCategory.INVALID_REQUEST,
                )

        # Raise outside the exception handler so the raw httpx exception is
        # not retained as context on the public-safe exception.
        if provider_error is not None:
            raise provider_error
        if not 200 <= response.status_code <= 299:
            raise ProviderCallError(
                http_status=response.status_code,
                category=_http_error_category(response.status_code),
            )
        response_error: ProviderCallError | None = None
        try:
            data = response.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            tool_calls: list[ToolCall] = []
            for raw_call in message.get("tool_calls") or []:
                function = raw_call.get("function") or {}
                arguments = function.get("arguments") or "{}"
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                tool_calls.append(
                    ToolCall(
                        name=str(function.get("name", "")),
                        arguments=arguments if isinstance(arguments, dict) else {},
                    )
                )

            usage = data.get("usage") or {}
            tokens_used = int(
                usage.get("total_tokens")
                or (
                    int(usage.get("prompt_tokens", usage.get("input_tokens", 0)))
                    + int(usage.get("completion_tokens", usage.get("output_tokens", 0)))
                )
            )
            result = AgentRunResult(
                output=_message_text(message.get("content")),
                tool_calls=tool_calls,
                tokens_used=tokens_used,
                provider=self.name,
                # The response body ID is OpenAI-compatible but not required by
                # GitHub's Models contract. GitHub's documented REST request ID
                # header is the durable fallback receipt.
                raw_id=(
                    str(data.get("id"))
                    if data.get("id")
                    else response.headers.get("x-github-request-id")
                ),
            )
        except Exception:  # noqa: BLE001 - provider-controlled response must be reduced safely
            response_error = ProviderCallError(
                http_status=response.status_code,
                category=ProviderErrorCategory.PROVIDER_UNAVAILABLE,
            )
        if response_error is not None:
            raise response_error
        return result
