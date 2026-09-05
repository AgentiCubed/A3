"""Generic OpenAI-compatible chat-completions adapter.

Several providers expose the same ``POST {base_url}/chat/completions`` request
and response shape: Google's Gemini via the AI Studio OpenAI-compatibility
endpoint, Ollama's local server, OpenAI itself, and — until its retirement —
GitHub Models. One adapter parameterised by base URL and credential reference
therefore covers all of them, so adding a provider is configuration rather than
new code (ADR-0003: providers are adapters, never architecture).

The application still receives only a credential *reference*. The secret is
resolved at call time and is never persisted, logged, or returned.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from app.core.secrets import CredentialNotAllowed, CredentialNotConfigured, resolve_credential
from app.orchestration.ports import (
    AgentRunRequest,
    AgentRunResult,
    ProviderCallError,
    ProviderErrorCategory,
    ToolCall,
)

_DEFAULT_MAX_TOKENS = 2048


def message_text(content: Any) -> str:
    """Reduce an OpenAI-shaped message ``content`` to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def http_error_category(status_code: int) -> ProviderErrorCategory:
    """Map an HTTP status to a bounded, public-safe failure reason."""
    if status_code == 401:
        return ProviderErrorCategory.AUTHENTICATION
    if status_code == 403:
        return ProviderErrorCategory.AUTHORIZATION
    # 404 (never existed) and 410 (permanently withdrawn) are both "this
    # endpoint or model is not there". GitHub Models' 2026-07-30 retirement
    # returned 410 and was reported to operators as a generic invalid_request,
    # which cost hours of misdiagnosis; keep the distinction visible.
    if status_code in {404, 410}:
        return ProviderErrorCategory.NOT_FOUND
    if status_code in {408, 504}:
        return ProviderErrorCategory.TIMEOUT
    if status_code == 429:
        return ProviderErrorCategory.RATE_LIMITED
    if 400 <= status_code <= 499:
        return ProviderErrorCategory.INVALID_REQUEST
    return ProviderErrorCategory.PROVIDER_UNAVAILABLE


class OpenAICompatibleProvider:
    """Call any OpenAI-compatible ``/chat/completions`` endpoint.

    ``requires_credential=False`` supports local servers (Ollama) that accept
    unauthenticated requests; a credential is still sent when one is
    configured, since some local deployments front the server with a proxy.
    """

    # HTTP status codes that indicate a transient server-side problem and are
    # safe to retry immediately (without counting against max_attempts).
    _TRANSIENT_5XX: frozenset[int] = frozenset({500, 502, 503})

    # Longest single in-adapter sleep honoring a Retry-After header. The
    # attempt's outer time budget (execute_task's timeout_s) wraps this whole
    # call, so a provider asking for a 60s wait must not be obeyed literally —
    # the dispatch loop's between-attempt delay and re-dispatch handle waits
    # longer than this.
    _RATE_LIMIT_MAX_DELAY: float = 15.0

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        default_model: str,
        default_credential_ref: str,
        requires_credential: bool = True,
        model_prefix: str = "",
        extra_headers: dict[str, str] | None = None,
        timeout_seconds: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
        transient_retry_delays: list[float] | None = None,
        rate_limit_retry_delays: list[float] | None = None,
    ) -> None:
        self.name = name
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._default_model = default_model
        self._default_credential_ref = default_credential_ref
        self._requires_credential = requires_credential
        self._model_prefix = model_prefix
        self._extra_headers = dict(extra_headers or {})
        self._timeout = timeout_seconds
        self._transport = transport
        # Delays (seconds) between successive retries on transient 5xx errors.
        # The number of retries equals len(transient_retry_delays).
        self._transient_retry_delays: list[float] = (
            [1.0, 2.0] if transient_retry_delays is None else list(transient_retry_delays)
        )
        # Fallback delays for 429 responses when no usable Retry-After header
        # is present. The free Gemini tier enforces per-minute quotas, so a
        # short in-adapter wait often clears the window without burning an
        # operator-visible attempt.
        self._rate_limit_retry_delays: list[float] = (
            [2.0, 5.0] if rate_limit_retry_delays is None else list(rate_limit_retry_delays)
        )

    def _rate_limit_delay(self, response: httpx.Response, fallback: float) -> float:
        """Delay before retrying a 429: Retry-After when sane, else fallback.

        Only the integer-seconds form of Retry-After is honored (the HTTP-date
        form is rare on model APIs and not worth parsing here), and it is
        capped so a provider cannot park the whole attempt budget on a sleep.
        """
        raw = response.headers.get("retry-after", "")
        try:
            seconds = float(raw)
        except ValueError:
            return fallback
        if seconds <= 0:
            return fallback
        return min(seconds, self._RATE_LIMIT_MAX_DELAY)

    def _resolve_token(self, request: AgentRunRequest) -> str | None:
        # Every raise below happens *outside* its except block so the public
        # error carries no __context__ chain back to the original exception,
        # whose message can name the credential reference.
        ref = request.credential_ref or self._default_credential_ref
        token: str | None = None
        error: ProviderCallError | None = None
        try:
            token = resolve_credential(ref)
        except CredentialNotAllowed:
            # A ref outside ALLOWED_CREDENTIAL_REFS is a policy refusal, not a
            # missing secret — even for providers that would accept anonymous
            # calls, because the config asked us to read a forbidden env var.
            error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.AUTHORIZATION,
            )
        except CredentialNotConfigured:
            if self._requires_credential:
                error = ProviderCallError(
                    http_status=None,
                    category=ProviderErrorCategory.AUTHENTICATION,
                )
        except Exception:  # noqa: BLE001 - malformed references must not escape
            error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.INVALID_REQUEST,
            )
        if error is not None:
            raise error
        return token

    def _qualified_model(self, model: str) -> str:
        """Apply a provider's namespace to a bare model name.

        Gemini's catalog names every model ``models/<id>`` and returns 404 for
        the bare form, so an operator who reasonably types ``gemini-2.5-flash``
        would get "no such model" with nothing pointing at the missing prefix.
        Accept both spellings rather than make the operator know.
        """
        if self._model_prefix and not model.startswith(self._model_prefix):
            return f"{self._model_prefix}{model}"
        return model

    def _build(
        self, request: AgentRunRequest, *, token: str | None, with_response_format: bool
    ) -> tuple[dict[str, Any], dict[str, str]]:
        try:
            messages: list[dict[str, str]] = []
            if request.system:
                messages.append({"role": "system", "content": request.system})
            messages.append({"role": "user", "content": request.prompt})

            payload: dict[str, Any] = {
                "model": self._qualified_model(request.model or self._default_model),
                "max_tokens": int(request.params.get("max_tokens", _DEFAULT_MAX_TOKENS)),
                "messages": messages,
            }
            if "temperature" in request.params:
                payload["temperature"] = request.params["temperature"]
            response_format = request.params.get("response_format")
            if response_format and with_response_format:
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
                "accept": "application/json",
                "content-type": "application/json",
                **self._extra_headers,
            }
            if token:
                headers["authorization"] = f"Bearer {token}"
            build_error: ProviderCallError | None = None
        except Exception:  # noqa: BLE001 - request inputs must not escape in errors
            build_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.INVALID_REQUEST,
            )
        if build_error is not None:
            raise build_error
        return payload, headers

    async def _post(
        self, client: httpx.AsyncClient, payload: dict[str, Any], headers: dict[str, str]
    ) -> httpx.Response:
        response: httpx.Response | None = None
        transport_error: ProviderCallError | None = None
        try:
            response = await client.post(self._url, json=payload, headers=headers)
        except httpx.TimeoutException:
            transport_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.TIMEOUT,
            )
        except httpx.RequestError:
            transport_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.NETWORK_ERROR,
            )
        except Exception:  # noqa: BLE001 - request construction must not expose inputs
            transport_error = ProviderCallError(
                http_status=None,
                category=ProviderErrorCategory.INVALID_REQUEST,
            )
        # Raised outside the handler so the httpx exception is not retained as
        # context (it can carry the URL and request internals).
        if transport_error is not None:
            raise transport_error
        assert response is not None  # noqa: S101 - narrowing after the guard above
        return response

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        token = self._resolve_token(request)
        wants_response_format = bool(request.params.get("response_format"))
        payload, headers = self._build(request, token=token, with_response_format=True)

        async with httpx.AsyncClient(
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await self._post(client, payload, headers)

            def _format_rejected(status: int) -> bool:
                # Structured-output support is not advertised uniformly across
                # OpenAI-compatible servers or across models within one
                # server, so a 4xx on a request that carried response_format
                # is retried once without it. 429 is excluded: rate limiting
                # says nothing about response_format, and the old blanket 4xx
                # check made a rate-limited call *immediately* fire a second
                # request into the same exhausted quota window.
                return wants_response_format and 400 <= status <= 499 and status != 429

            if _format_rejected(response.status_code):
                retry_payload, retry_headers = self._build(
                    request, token=token, with_response_format=False
                )
                response = await self._post(client, retry_payload, retry_headers)
            else:
                retry_payload, retry_headers = payload, headers

            # Retry transient failures before surfacing anything to the
            # dispatch loop, each class against its own budget: 5xx blips use
            # transient_retry_delays as-is; 429s wait out the quota window,
            # honoring a sane Retry-After header (capped) over the configured
            # fallback delay. In-adapter retries do not consume an
            # operator-visible attempt. Retries reuse the payload that was
            # effective at the end of the previous exchange (with or without
            # response_format, whichever the server last accepted).
            effective_payload, effective_headers = retry_payload, retry_headers
            transient_budget = list(self._transient_retry_delays)
            rate_limit_budget = list(self._rate_limit_retry_delays)
            while True:
                if response.status_code in self._TRANSIENT_5XX and transient_budget:
                    delay = transient_budget.pop(0)
                elif response.status_code == 429 and rate_limit_budget:
                    delay = self._rate_limit_delay(response, rate_limit_budget.pop(0))
                else:
                    break
                await asyncio.sleep(delay)
                response = await self._post(client, effective_payload, effective_headers)
                if _format_rejected(response.status_code):
                    fallback_payload, fallback_headers = self._build(
                        request, token=token, with_response_format=False
                    )
                    response = await self._post(client, fallback_payload, fallback_headers)
                    effective_payload, effective_headers = fallback_payload, fallback_headers

        if not 200 <= response.status_code <= 299:
            raise ProviderCallError(
                http_status=response.status_code,
                category=http_error_category(response.status_code),
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
                output=message_text(message.get("content")),
                tool_calls=tool_calls,
                tokens_used=tokens_used,
                provider=self.name,
                raw_id=str(data["id"]) if data.get("id") else None,
            )
        except Exception:  # noqa: BLE001 - provider-controlled response must be reduced safely
            response_error = ProviderCallError(
                http_status=response.status_code,
                category=ProviderErrorCategory.PROVIDER_UNAVAILABLE,
            )
        if response_error is not None:
            raise response_error
        return result


class RetiredProvider:
    """A provider that no longer exists, kept so stored agents fail readably.

    Deleting a retired adapter would make every agent row still naming it fail
    with an opaque unknown-provider error at dispatch. Keeping a tombstone that
    raises the normal typed provider error preserves the diagnostic path, and
    ``registry.available_providers()`` omits it so new agents cannot select it.
    """

    def __init__(self, *, name: str, retired_on: str, replacement: str) -> None:
        self.name = name
        self.retired_on = retired_on
        self.replacement = replacement

    @property
    def guidance(self) -> str:
        return (
            f"provider {self.name!r} was retired on {self.retired_on}; "
            f"reassign affected agents to {self.replacement!r}"
        )

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        # 410 Gone is what a retired upstream returns, and mapping it to
        # not_found makes the stored diagnostic say so plainly.
        raise ProviderCallError(
            http_status=410,
            category=ProviderErrorCategory.NOT_FOUND,
        )
