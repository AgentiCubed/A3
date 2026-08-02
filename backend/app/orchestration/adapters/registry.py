"""Provider adapter registry.

Maps a provider *name* to a concrete ``AgentAdapter``. Orchestration selects an
adapter by the agent's ``provider`` field; it never imports a vendor SDK
directly. Add new providers here (ADR-0003).

Most live providers are instances of the one OpenAI-compatible adapter, so a
new endpoint is a registry entry rather than a new module. Retired providers
stay registered as tombstones (see ``RetiredProvider``) but are excluded from
``available_providers()``.
"""

from __future__ import annotations

from app.orchestration.adapters.anthropic_provider import AnthropicProvider
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.adapters.openai_compatible_provider import (
    OpenAICompatibleProvider,
    RetiredProvider,
)
from app.orchestration.ports import AgentAdapter

# Google AI Studio's OpenAI-compatibility endpoint. Free tier, no card; that
# free tier may use prompts to improve Google's models, so confidential work
# belongs on a local provider instead.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"

# Ollama on the operator's own machine: no credential, no quota, no network.
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_DEFAULT_MODEL = "llama3.2"

_REGISTRY: dict[str, AgentAdapter] = {
    MockProvider.name: MockProvider(),
    AnthropicProvider.name: AnthropicProvider(),
    "gemini": OpenAICompatibleProvider(
        name="gemini",
        base_url=GEMINI_BASE_URL,
        default_model=GEMINI_DEFAULT_MODEL,
        default_credential_ref="GEMINI_API_KEY",
    ),
    "ollama": OpenAICompatibleProvider(
        name="ollama",
        base_url=OLLAMA_BASE_URL,
        default_model=OLLAMA_DEFAULT_MODEL,
        default_credential_ref="OLLAMA_API_KEY",
        requires_credential=False,
    ),
    # GitHub Models — playground, catalog, and inference API — was fully
    # retired by GitHub on 2026-07-30; the endpoint returns 410 Gone. Kept as
    # a tombstone so pre-existing agent rows fail with a typed, readable error
    # instead of an opaque unknown-provider crash.
    "github_models": RetiredProvider(
        name="github_models",
        retired_on="2026-07-30",
        replacement="gemini",
    ),
}


class UnknownProvider(Exception):
    pass


def get_adapter(name: str | None) -> AgentAdapter:
    """Return the adapter for ``name`` (defaults to the deterministic mock)."""
    key = name or MockProvider.name
    adapter = _REGISTRY.get(key)
    if adapter is None:
        raise UnknownProvider(key)
    return adapter


def retirement_guidance(name: str | None) -> str | None:
    """Return migration guidance when ``name`` names a retired provider."""
    adapter = _REGISTRY.get(name or MockProvider.name)
    if isinstance(adapter, RetiredProvider):
        return adapter.guidance
    return None


def available_providers() -> list[str]:
    """Provider names selectable for new agents (retired ones excluded)."""
    return sorted(
        name for name, adapter in _REGISTRY.items() if not isinstance(adapter, RetiredProvider)
    )
