"""Shared test fixtures.

Backend tests run against a file-backed SQLite database (async, NullPool so each
checkout is a fresh connection — safe across the TestClient portal loop and the
pytest-asyncio loop). The real Postgres engine is never touched; the ``db_session``
dependency is overridden.
"""

from __future__ import annotations

import asyncio
import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401  - register models on Base.metadata
from app.api.deps import db_session
from app.db.base import Base
from app.main import app

# Keep concurrent local/CI pytest processes from deleting one another's SQLite
# database. Tests in this process still share one database through the
# session-scoped fixture.
TEST_DB_PATH = f"/tmp/agenticubed_test_{os.getpid()}.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def _override_db_session():
    async with TestSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
def _fresh_auth_rate_limit():
    """Give every test its own rate-limit window.

    All TestClient requests share one fake client IP, so without a per-test
    reset the auth limiter's fixed window would leak budget between tests and
    fail whichever unlucky test crossed the threshold. Rate-limit tests that
    need a tight budget set AUTH_RATE_LIMIT_PER_MINUTE themselves and reset
    again.
    """
    from app.core.rate_limit import reset_auth_limiter, reset_preflight_limiter

    reset_auth_limiter()
    reset_preflight_limiter()
    yield
    reset_auth_limiter()
    reset_preflight_limiter()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    app.dependency_overrides[db_session] = _override_db_session
    yield
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c


@pytest.fixture()
async def session():
    async with TestSessionFactory() as s:
        yield s
