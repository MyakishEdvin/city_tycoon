"""
/help, /settings, and placeholder responses for commands/buttons whose real
implementation lands in later phases (business, inventory, quests,
leaderboard, events). The city/buildings feature has its own module,
bot/handlers/city.py, once it grew past a one-line placeholder.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main_menu import (
    BTN_BUSINESS,
    BTN_EVENTS,
    BTN_INVENTORY,
    BTN_LEADERBOARD,
    BTN_QUESTS,
    OPEN_CITY_LABEL,
)
from database.models.user_service import UserService

router = Router(name="common")

HELP_TEXT = (
    "🏙 <b>CITY TYCOON — Помощь</b>\n\n"
    "/start — регистрация или возврат в город\n"
    "/profile — ваша статистика\n"
    "/city — ваш город и здания\n"
    "/business — управление бизнесом\n"
    "/inventory — ваш инвентарь\n"
    "/tasks — ваши задания\n"
    "/transactions — история операций\n"
    "/rating — таблица лидеров\n"
    "/events — текущие события\n"
    "/language — сменить язык\n"
    "/settings — настройки уведомлений\n"
    "/help — это сообщение\n\n"
    "Используйте меню ниже или нажмите 🏙 ОТКРЫТЬ ГОРОД, чтобы играть."
)

_COMING_SOON = {
    "business": "💼 <b>Бизнес</b>\n\nУправление бизнесом появится в следующем обновлении!",
    "inventory": "📦 <b>Инвентарь</b>\n\nВаш инвентарь пока пуст — скоро здесь что-то появится!",
    "tasks": "🎯 <b>Задания</b>\n\nЕжедневные и еженедельные задания скоро появятся!",
    "rating": "🏆 <b>Рейтинг</b>\n\nТаблица лидеров скоро появится!",
    "events": "🔥 <b>События</b>\n\nЕженедельные события скоро появятся!",
}


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("settings"))
async def cmd_settings(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    language_line = (
        f"🌐 Язык: {user.language} (используйте /language, чтобы изменить)\n" if user else ""
    )
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"{language_line}"
        f"Настройки уведомлений появятся в следующем обновлении."
    )


@router.message(Command("business"))
@router.message(F.text == BTN_BUSINESS)
async def business_placeholder(message: Message) -> None:
    await message.answer(_COMING_SOON["business"])


@router.message(Command("inventory"))
@router.message(F.text == BTN_INVENTORY)
async def inventory_placeholder(message: Message) -> None:
    await message.answer(_COMING_SOON["inventory"])


@router.message(Command("tasks"))
@router.message(F.text == BTN_QUESTS)
async def tasks_placeholder(message: Message) -> None:
    await message.answer(_COMING_SOON["tasks"])


@router.message(Command("rating"))
@router.message(F.text == BTN_LEADERBOARD)
async def rating_placeholder(message: Message) -> None:
    await message.answer(_COMING_SOON["rating"])


@router.message(Command("events"))
@router.message(F.text == BTN_EVENTS)
async def events_placeholder(message: Message) -> None:
    await message.answer(_COMING_SOON["events"])


@router.message(F.text == OPEN_CITY_LABEL)
async def open_city_fallback(message: Message) -> None:
    """
    Only fires when WEBAPP_URL isn't configured — otherwise this button
    is a real WebApp button and Telegram opens the Mini App directly
    without sending a message at all.
    """
    if settings.webapp_configured:
        return
    await message.answer(
        "🏙 Мини-приложение пока не развёрнуто в этом окружении. "
        "Укажите WEBAPP_URL в .env, когда оно будет готово."
    )