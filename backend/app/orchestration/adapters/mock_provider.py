"""Deterministic mock provider for tests and offline development.

Produces stable, reproducible output for a given request (no network, no
randomness), so deterministic tests never call a live provider (assumption A15).
Token/cost figures are derived deterministically from input length.

Control markers (dual-use: failure-path tests AND the Phase-8 deliberate failure):
- ``[[FAIL]]`` anywhere in the prompt -> raises, simulating an execution error.
- ``[[SLEEP:<seconds>]]`` -> awaits that many seconds (drives timeout tests).
"""

from __future__ import annotations

import asyncio
import hashlib
import re

from app.orchestration.ports import AgentRunRequest, AgentRunResult

_SLEEP_RE = re.compile(r"\[\[SLEEP:([0-9]+(?:\.[0-9]+)?)\]\]")


class MockProviderError(RuntimeError):
    """Raised by MockProvider when the prompt contains the [[FAIL]] marker."""


class MockProvider:
    name = "mock"

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        prompt = request.prompt

        sleep_match = _SLEEP_RE.search(prompt)
        if sleep_match:
            await asyncio.sleep(float(sleep_match.group(1)))

        if "[[FAIL]]" in prompt:
            raise MockProviderError("simulated execution failure")

        digest = hashlib.sha256(f"{request.system or ''}\n{prompt}".encode()).hexdigest()
        output = f"[mock:{request.model or 'default'}] response::{digest[:16]}"
        tokens = max(1, len(prompt) // 4)
        return AgentRunResult(
            output=output,
            tokens_used=tokens,
            cost_estimate=round(tokens * 1e-6, 8),
            provider=self.name,
            raw_id=digest[:32],
        )
