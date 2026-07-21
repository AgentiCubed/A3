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

from app.core.secrets import resolve_credential
from app.orchestration.ports import AgentRunRequest, AgentRunResult, ToolCall

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
        token = resolve_credential(request.credential_ref or _DEFAULT_CREDENTIAL_REF)
        model = request.model or _DEFAULT_MODEL
        messages: list[dict[str, str]] = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": int(request.params.get("max_tokens", 128)),
            "messages": messages,
        }
        if "temperature" in request.params:
            payload["temperature"] = request.params["temperature"]
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
        async with httpx.AsyncClient(
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await client.post(_API_URL, json=payload, headers=headers)
            response.raise_for_status()
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
        return AgentRunResult(
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
