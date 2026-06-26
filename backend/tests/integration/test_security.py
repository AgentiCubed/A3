"""Security hardening: response headers and the production secret guard."""

from __future__ import annotations

import pytest

from app.core.config import Settings


def test_security_headers_present(client):
    resp = client.get("/healthz")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "no-referrer"
    assert "content-security-policy" in resp.headers


def test_production_rejects_default_secret():
    prod = Settings(environment="production")  # default insecure secret
    with pytest.raises(RuntimeError):
        prod.assert_production_safe()


def test_production_accepts_strong_secret():
    prod = Settings(environment="production", secret_key="a-strong-unique-production-secret-value")
    prod.assert_production_safe()  # does not raise


def test_cors_origin_list_parsing():
    s = Settings(cors_origins="https://a.example, https://b.example")
    assert s.cors_origin_list == ["https://a.example", "https://b.example"]
