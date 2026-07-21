"""Boot a hermetic backend for browser e2e tests.

SQLite file database (recreated fresh on every boot), in-memory event bus,
inline workflow engine, mock provider — the same hermetic surface the
integration suite uses, but served over real HTTP so Playwright can drive the
governed loop through the actual UI. No Postgres, Redis, broker, or live
provider is required (assumption A15 holds: deterministic CI, no live model).

Run from the backend directory: ``python tools/run_e2e_backend.py``.
"""

from __future__ import annotations

import asyncio
import os
import pathlib

# Test-only scratch database; recreated on every boot, never holds real data.
DB_PATH = os.environ.get("E2E_DB_PATH", "/tmp/agenticubed-e2e.db")  # noqa: S108
# Must be set before any app module import — the engine binds at import time.
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")
os.environ.setdefault("EVENT_BUS_BACKEND", "memory")
os.environ.setdefault("WORKFLOW_ENGINE_BACKEND", "inline")
os.environ.setdefault("DEFAULT_PROVIDER", "mock")


def main() -> None:
    for suffix in ("", "-wal", "-shm"):
        stale = pathlib.Path(DB_PATH + suffix)
        if stale.exists():
            stale.unlink()

    import app.models  # noqa: F401 - register models on Base.metadata
    from app.db.base import Base
    from app.db.session import engine

    async def _create_schema() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_create_schema())

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=int(os.environ.get("E2E_BACKEND_PORT", "8000")),
        log_level="warning",
    )


if __name__ == "__main__":
    main()
