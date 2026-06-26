"""Provider adapter registry.

Maps a provider *name* to a concrete ``AgentAdapter``. Orchestration selects an
adapter by the agent's ``provider`` field; it never imports a vendor SDK
directly. Add new providers here (ADR-0003).
"""

from __future__ import annotations

from app.orchestration.adapters.anthropic_provider import AnthropicProvider
from app.orchestration.adapters.mock_provider import MockProvider
from app.orchestration.ports import AgentAdapter

_REGISTRY: dict[str, AgentAdapter] = {
    MockProvider.name: MockProvider(),
    AnthropicProvider.name: AnthropicProvider(),
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


def available_providers() -> list[str]:
    return sorted(_REGISTRY.keys())
