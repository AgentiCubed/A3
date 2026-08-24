"""Fixed-window auth rate limiting."""

from __future__ import annotations

from app.core.rate_limit import _WINDOW_SECONDS, RateLimiter


def test_allows_up_to_the_limit_then_refuses():
    limiter = RateLimiter(limit_per_minute=3)
    assert limiter.allow("login:1.2.3.4", now=0.0)
    assert limiter.allow("login:1.2.3.4", now=1.0)
    assert limiter.allow("login:1.2.3.4", now=2.0)
    assert not limiter.allow("login:1.2.3.4", now=3.0)


def test_window_expiry_restores_budget():
    limiter = RateLimiter(limit_per_minute=1)
    assert limiter.allow("k", now=0.0)
    assert not limiter.allow("k", now=10.0)
    assert limiter.allow("k", now=_WINDOW_SECONDS + 0.1)


def test_keys_are_independent():
    limiter = RateLimiter(limit_per_minute=1)
    assert limiter.allow("login:1.2.3.4", now=0.0)
    assert limiter.allow("login:5.6.7.8", now=0.0)
    assert limiter.allow("register:1.2.3.4", now=0.0)
    assert not limiter.allow("login:1.2.3.4", now=1.0)


def test_zero_or_negative_limit_disables():
    limiter = RateLimiter(limit_per_minute=0)
    for i in range(50):
        assert limiter.allow("k", now=float(i))


def test_retry_after_counts_down_within_the_window():
    limiter = RateLimiter(limit_per_minute=1)
    limiter.allow("k", now=0.0)
    assert limiter.retry_after_seconds("k", now=0.0) == int(_WINDOW_SECONDS) + 1
    assert limiter.retry_after_seconds("k", now=50.0) <= 11
    assert limiter.retry_after_seconds("k", now=59.5) >= 1


def test_unknown_key_suggests_full_window():
    limiter = RateLimiter(limit_per_minute=1)
    assert limiter.retry_after_seconds("never-seen", now=0.0) == int(_WINDOW_SECONDS)
