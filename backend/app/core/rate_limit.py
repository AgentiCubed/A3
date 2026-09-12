"""Fixed-window rate limiting for auth and provider preflight endpoints.

In-process and per-worker by design: the goal is stopping credential
brute-force and registration floods on a single-node deployment, not precise
global quotas. A multi-instance deployment shares nothing between workers, so
each worker enforces the limit independently — still a hard brake on abuse,
just N× looser. Move the counters to Redis if that ever matters.

Keys are (scope, client-ip). Behind the bundled Caddy proxy the client IP
arrives in X-Forwarded-For; only the FIRST hop is trusted, and only because the
proxy overwrites the header. Windows are wall-clock aligned via monotonic time
so clock changes cannot reset counters.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_WINDOW_SECONDS = 60.0


@dataclass
class _Window:
    started: float = 0.0
    count: int = 0


@dataclass
class RateLimiter:
    """Fixed-window counter; ``allow`` returns False once a window is full."""

    limit_per_minute: int
    _windows: dict[str, _Window] = field(default_factory=lambda: defaultdict(_Window))

    def allow(self, key: str, *, now: float | None = None) -> bool:
        if self.limit_per_minute <= 0:  # disabled (tests, explicit opt-out)
            return True
        current = time.monotonic() if now is None else now
        window = self._windows[key]
        if current - window.started >= _WINDOW_SECONDS:
            window.started = current
            window.count = 0
        window.count += 1
        # Opportunistic cleanup keeps the dict from growing unboundedly under
        # address-rotating abuse; expired windows carry no information.
        if len(self._windows) > 10_000:
            expired = [
                k for k, w in self._windows.items() if current - w.started >= _WINDOW_SECONDS
            ]
            for k in expired:
                del self._windows[k]
        return window.count <= self.limit_per_minute

    def retry_after_seconds(self, key: str, *, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        window = self._windows.get(key)
        if window is None:
            return int(_WINDOW_SECONDS)
        remaining = _WINDOW_SECONDS - (current - window.started)
        return max(1, int(remaining) + 1)


_auth_limiter: RateLimiter | None = None
_preflight_limiter: RateLimiter | None = None


def _limiter() -> RateLimiter:
    global _auth_limiter  # noqa: PLW0603 - process-wide counter is the point
    if _auth_limiter is None:
        _auth_limiter = RateLimiter(limit_per_minute=get_settings().auth_rate_limit_per_minute)
    return _auth_limiter


def _preflight() -> RateLimiter:
    global _preflight_limiter  # noqa: PLW0603 - process-wide counter is the point
    if _preflight_limiter is None:
        # Reuse the existing deployment abuse-control budget, but keep a
        # separate counter so auth traffic never consumes provider-preflight
        # quota and vice versa.
        _preflight_limiter = RateLimiter(
            limit_per_minute=get_settings().auth_rate_limit_per_minute
        )
    return _preflight_limiter


def reset_auth_limiter() -> None:
    """Drop all counters (tests)."""
    global _auth_limiter  # noqa: PLW0603
    _auth_limiter = None


def reset_preflight_limiter() -> None:
    """Drop all preflight counters (tests)."""
    global _preflight_limiter  # noqa: PLW0603
    _preflight_limiter = None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request, scope: str) -> None:
    """Raise 429 (with Retry-After) when this client exceeds the auth budget."""
    limiter = _limiter()
    key = f"{scope}:{client_ip(request)}"
    if not limiter.allow(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many requests; slow down",
            headers={"Retry-After": str(limiter.retry_after_seconds(key))},
        )


def enforce_preflight_rate_limit(request: Request) -> None:
    """Raise 429 when this client exceeds the provider preflight budget."""
    limiter = _preflight()
    key = f"providers_preflight:{client_ip(request)}"
    if not limiter.allow(key):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many requests; slow down",
            headers={"Retry-After": str(limiter.retry_after_seconds(key))},
        )
