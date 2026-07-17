"""Anthropic (Claude) provider adapter — the first real ModelProvider.

Implements the provider-neutral ``AgentAdapter`` port over the Anthropic Messages
API. Domain code never imports this directly; it is selected by name through the
registry (ADR-0003).

Secrets: the API key is resolved from an env-var *key* (``credential_ref``) at
call time via ``resolve_credential`` and is never logged, persisted, or returned.
The credential is resolved BEFORE any network work, so a missing key fails fast
and deterministically.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.secrets import resolve_credential
from app.orchestration.ports import AgentRunRequest, AgentRunResult

_DEFAULT_MODEL = "claude-sonnet-4-6"
_DEFAULT_CREDENTIAL_REF = "ANTHROPIC_API_KEY"
_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"

# Cost per token in USD for each model (input_cost, output_cost).
# Rates from Anthropic public pricing; update when pricing changes.
_RATE_CARD: dict[str, tuple[float, float]] = {
    "claude-opus-4-5":        (15.00 / 1_000_000, 75.00 / 1_000_000),
    "claude-opus-4":          (15.00 / 1_000_000, 75.00 / 1_000_000),
    "claude-sonnet-4-6":      (3.00  / 1_000_000, 15.00 / 1_000_000),
    "claude-sonnet-4-5":      (3.00  / 1_000_000, 15.00 / 1_000_000),
    "claude-sonnet-3-7":      (3.00  / 1_000_000, 15.00 / 1_000_000),
    "claude-haiku-3-5":       (0.80  / 1_000_000,  4.00 / 1_000_000),
    "claude-haiku-3":         (0.25  / 1_000_000,  1.25 / 1_000_000),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return USD cost estimate; falls back to sonnet-4-6 rates for unknown models."""
    in_rate, out_rate = _RATE_CARD.get(model, _RATE_CARD[_DEFAULT_MODEL])
    return round(input_tokens * in_rate + output_tokens * out_rate, 8)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self._timeout = timeout_seconds

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        # Resolve the credential first — fail fast, no network if unset.
        api_key = resolve_credential(request.credential_ref or _DEFAULT_CREDENTIAL_REF)
        model = request.model or _DEFAULT_MODEL

        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": int(request.params.get("max_tokens", 1024)),
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system:
            payload["system"] = request.system
        if "temperature" in request.params:
            payload["temperature"] = request.params["temperature"]

        headers = {
            "x-api-key": api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        tokens = input_tokens + output_tokens
        return AgentRunResult(
            output=text,
            tokens_used=tokens,
            cost_estimate=_estimate_cost(model, input_tokens, output_tokens),
            provider=self.name,
            raw_id=str(data.get("id")) if data.get("id") else None,
        )
