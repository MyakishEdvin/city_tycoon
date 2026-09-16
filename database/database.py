"""
Async database engine and session management.

This module is the single source of truth for how every part of the
project (bot, backend API, background jobs) talks to PostgreSQL. It is
intentionally framework-agnostic: aiogram middlewares, FastAPI dependencies,
and standalone scripts can all reuse `AsyncSessionLocal`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from bot.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model in the project."""
    pass


engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context-managed session for use outside of aiogram/FastAPI DI
    (e.g. in scripts, tests, or scheduled jobs added in later phases).
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """
    Create tables directly from the ORM metadata.

    This is a convenience for local development only. In every real
    environment (including Phase 1 onward once Alembic is initialized),
    schema changes should go through Alembic migrations, not this
    function, so history stays consistent.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Cleanly close all pooled connections on shutdown."""
    await engine.dispose()
