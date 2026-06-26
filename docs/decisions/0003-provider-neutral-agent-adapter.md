# ADR-0003: Provider-neutral AgentAdapter as the only model seam

- **Status:** Accepted
- **Date:** 2026-06-25

## Context
The platform must not couple orchestration to a single model provider. Multiple
providers (and local/dev providers) must be interchangeable, and deterministic
tests must run without any network call.

## Decision
All model interaction goes through one port:

```python
class AgentAdapter(Protocol):
    async def run(self, request: AgentRunRequest) -> AgentRunResult: ...
    # request: prompt/messages, tool schemas, model id, params, run context
    # result:  output, tool calls, tokens_used, cost_estimate, raw provider id
```

Concrete adapters:
- `MockProvider` — deterministic, no network; the only adapter used in CI tests.
- `AnthropicAdapter` — first functional real provider (Claude).
- Additional providers implement the same port; no other layer imports a
  provider SDK.

Credentials are passed by **reference** (env var key), resolved at call time,
and never written to executions, artifacts, logs, or audit rows (see
`docs/security-model.md` §7).

## Consequences
- Swapping/adding providers is local to `app/orchestration/adapters`.
- Tests are reproducible and offline by default (ADR honored by A15).
- The adapter result is normalized (tokens, cost) so metrics and remediation are
  provider-agnostic.
