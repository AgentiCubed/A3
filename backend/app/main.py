"""FastAPI application entrypoint.

Thin controllers only. Business logic lives in app/services and is reached via
dependency injection. This Phase-1 app wires logging, health checks, and the
versioned API router.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("app.main")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "X-XSS-Protection": "0",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.assert_production_safe()  # refuse insecure default secret in prod
    log.info("startup", environment=settings.environment, version=__version__)
    yield
    log.info("shutdown")


app = FastAPI(
    title="AgentiCubed API",
    version=__version__,
    description="Agentic project-orchestration platform.",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    """Liveness: process is up. No external dependencies checked."""
    return {"status": "ok", "version": __version__}


@app.get("/readyz", tags=["health"])
async def readyz() -> dict[str, object]:
    """Readiness: database and Redis reachable."""
    from app.db.session import ping as db_ping

    checks: dict[str, str] = {}
    ok = True

    try:
        await db_ping()
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001 - report any failure as not-ready
        checks["database"] = f"error: {type(exc).__name__}"
        ok = False

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {type(exc).__name__}"
        ok = False

    return {"status": "ok" if ok else "degraded", "checks": checks}
