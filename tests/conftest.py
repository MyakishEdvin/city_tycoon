"""
Shared test fixtures.

Tests never touch the real PostgreSQL instance: each test gets its own
fresh in-memory SQLite database via aiosqlite, created from the same
SQLAlchemy metadata used in production. The dummy env vars below only
exist to satisfy Settings validation at import time (bot.config requires
BOT_TOKEN/DATABASE_URL) — they are never actually connected to.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "0000000000:TEST-TOKEN-NOT-REAL")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://unused:unused@localhost/unused")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.database import Base
import database.models  # noqa: F401  (registers every model on Base.metadata)


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()
