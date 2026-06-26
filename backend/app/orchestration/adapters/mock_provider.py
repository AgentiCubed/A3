"""Deterministic mock provider for tests and offline development.

Produces stable, reproducible output for a given request (no network, no
randomness), so deterministic tests never call a live provider (assumption A15).
Token/cost figures are derived deterministically from input length.
"""

from __future__ import annotations

import hashlib

from app.orchestration.ports import AgentRunRequest, AgentRunResult


class MockProvider:
    name = "mock"

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        digest = hashlib.sha256(f"{request.system or ''}\n{request.prompt}".encode()).hexdigest()
        output = f"[mock:{request.model or 'default'}] response::{digest[:16]}"
        tokens = max(1, len(request.prompt) // 4)
        return AgentRunResult(
            output=output,
            tokens_used=tokens,
            cost_estimate=round(tokens * 1e-6, 8),
            provider=self.name,
            raw_id=digest[:32],
        )
