"""Prometheus /metrics endpoint and request-count middleware."""

from __future__ import annotations


def test_metrics_endpoint_exposes_request_counts(client):
    client.get("/api/v1/meta")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    # the /api/v1/meta hit above is counted under its route template
    assert '/api/v1/meta"' in body


def test_metrics_endpoint_does_not_count_itself(client):
    client.get("/metrics")
    body = client.get("/metrics").text
    assert 'route="/metrics"' not in body
