"""
Injects a fresh AsyncSession into every update's handler data.

Handlers receive it as a `session` kwarg and never construct sessions
themselves. One session per update means one implicit transaction scope
per update, which is exactly the boundary we want for correctness.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.database import AsyncSessionLocal


class DatabaseSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)
