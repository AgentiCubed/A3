"""Prometheus metrics: request counter/latency middleware + /metrics endpoint.

Deferred in docs/architecture.md §9 ("Prometheus endpoint deferred to Phase 7").
Route labels use the matched route *template* (``/api/v1/projects/{project_id}``),
never the raw path, so label cardinality stays bounded.
"""

from __future__ import annotations

import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter(
    "http_requests_total",
    "HTTP requests processed",
    labelnames=("method", "route", "status"),
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    labelnames=("method", "route"),
)

_UNTRACKED = {"/metrics", "/healthz", "/readyz"}

#: The single mount prefix of the versioned API. Included routers report their
#: path template relative to the mount, so the prefix is re-attached here.
_API_PREFIX = "/api/v1"


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if template is None:
        # No matched route (404s, scanners): a fixed label keeps cardinality bounded.
        return "unmatched"
    if request.url.path.startswith(_API_PREFIX + "/") and not template.startswith(_API_PREFIX):
        return _API_PREFIX + template
    return template


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        route = _route_template(request)
        if route not in _UNTRACKED:
            REQUEST_COUNT.labels(request.method, route, str(response.status_code)).inc()
            REQUEST_LATENCY.labels(request.method, route).observe(time.perf_counter() - start)
        return response


async def metrics_endpoint() -> Response:
    """Prometheus exposition endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
