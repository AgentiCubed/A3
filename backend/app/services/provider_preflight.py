"""Cheap, non-destructive provider credential and reachability preflight.

Surfaces authentication/configuration failures *before* a project run burns
attempts. Never logs or returns secret values, raw provider payloads, URLs, or
request bodies — only allowlisted status/category diagnostics and human copy.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.secrets import CredentialNotAllowed, CredentialNotConfigured
from app.orchestration.adapters.anthropic_provider import (
    _DEFAULT_MODEL as ANTHROPIC_DEFAULT_MODEL,
)
from app.orchestration.adapters.anthropic_provider import (
    AnthropicProvider,
)
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.adapters.openai_compatible_provider import (
    RetiredProvider,
    http_error_category,
)
from app.orchestration.adapters.registry import UnknownProvider, get_adapter, retirement_guidance
from app.orchestration.ports import (
    AgentRunRequest,
    ProviderCallError,
    ProviderErrorCategory,
    human_message_for,
)


@dataclass(frozen=True)
class PreflightResult:
    """Outcome of a single provider preflight check."""

    provider: str
    ok: bool
    message: str
    category: str | None = None
    http_status: int | None = None
    diagnostic: str | None = None
    model: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "ok": self.ok,
            "message": self.message,
            "category": self.category,
            "http_status": self.http_status,
            "diagnostic": self.diagnostic,
            "model": self.model,
        }


def _fail(
    provider: str,
    *,
    category: ProviderErrorCategory,
    http_status: int | None = None,
    extra: str | None = None,
    model: str | None = None,
) -> PreflightResult:
    err = ProviderCallError(http_status=http_status, category=category)
    message = err.operator_message if extra is None else f"{err.operator_message} — {extra}"
    return PreflightResult(
        provider=provider,
        ok=False,
        message=message,
        category=category.value,
        http_status=http_status,
        diagnostic=err.public_message,
        model=model,
    )


def _used_model(adapter: object, requested_model: str | None) -> str | None:
    if requested_model:
        return requested_model
    default_model = getattr(adapter, "_default_model", None)
    if default_model:
        return str(default_model)
    if isinstance(adapter, AnthropicProvider):
        return ANTHROPIC_DEFAULT_MODEL
    return None


async def preflight_provider(
    provider: str,
    *,
    model: str | None = None,
    credential_ref: str | None = None,
) -> PreflightResult:
    """Verify a provider is selectable and can accept a trivial call.

    The mock adapter always passes (no network). Retired providers fail with
    migration guidance. Live adapters run one max_tokens=1 ping so missing
    credentials, unknown models, and network failures surface before a project
    starts. Exceptions are reduced to allowlisted diagnostics only.
    """
    try:
        adapter = get_adapter(provider)
    except UnknownProvider:
        return _fail(
            provider,
            category=ProviderErrorCategory.NOT_FOUND,
            extra=f"unknown provider {provider!r}",
            model=model,
        )

    if isinstance(adapter, RetiredProvider):
        return _fail(
            provider,
            category=ProviderErrorCategory.NOT_FOUND,
            http_status=410,
            extra=adapter.guidance,
            model=model,
        )

    if isinstance(adapter, MockProvider):
        return PreflightResult(
            provider=adapter.name,
            ok=True,
            message="Mock provider is ready (deterministic, no network).",
            model=model or "mock",
        )

    request = AgentRunRequest(
        prompt="preflight",
        model=model,
        credential_ref=credential_ref,
        params={"max_tokens": 1},
    )
    try:
        await adapter.run(request)
    except ProviderCallError as exc:
        guidance = retirement_guidance(provider)
        extra = guidance
        return _fail(
            provider,
            category=exc.category,
            http_status=exc.http_status,
            extra=extra,
            model=model,
        )
    except CredentialNotConfigured:
        return _fail(
            provider,
            category=ProviderErrorCategory.AUTHENTICATION,
            model=model,
        )
    except CredentialNotAllowed:
        return _fail(
            provider,
            category=ProviderErrorCategory.AUTHORIZATION,
            model=model,
        )
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        category = (
            http_error_category(status_code)
            if status_code is not None
            else ProviderErrorCategory.PROVIDER_UNAVAILABLE
        )
        return _fail(
            provider,
            category=category,
            http_status=status_code,
            model=model,
        )
    except Exception:  # noqa: BLE001 - preflight must never leak raw exceptions
        return _fail(
            provider,
            category=ProviderErrorCategory.PROVIDER_UNAVAILABLE,
            model=model,
        )

    used_model = _used_model(adapter, model)
    return PreflightResult(
        provider=adapter.name,
        ok=True,
        message="Provider credential and endpoint responded successfully.",
        model=used_model,
    )


def describe_category(category: str | None) -> str | None:
    """Map a category string to human copy; unknown values return None."""
    if category is None:
        return None
    try:
        return human_message_for(ProviderErrorCategory(category))
    except ValueError:
        return None
