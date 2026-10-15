"""Async database session/engine and a FastAPI dependency.

A Unit-of-Work helper wraps important multi-write state transitions in a single
transaction (state change + audit event + execution row), per the architecture's
transactional-integrity requirement.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session; commits on success, rolls back on error."""
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def unit_of_work() -> AsyncIterator[AsyncSession]:
    """Explicit transactional scope for important state transitions."""
    async with SessionFactory() as session:
        async with session.begin():
            yield session


async def ping() -> bool:
    """Lightweight DB reachability check for /readyz."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True
