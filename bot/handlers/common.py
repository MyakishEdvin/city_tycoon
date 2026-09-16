"""
/help, /settings, and placeholder responses for commands/buttons whose real
implementation lands in later phases (city, business, inventory, quests,
leaderboard, events). Keeping them wired up now means the menu is fully
clickable from Phase 1 onward instead of dead buttons — each placeholder
will be replaced with real logic in its own phase.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.keyboards.main_menu import (
    BTN_BUSINESS,
    BTN_CITY,
    BTN_EVENTS,
    BTN_INVENTORY,
    BTN_LEADERBOARD,
    BTN_QUESTS,
    OPEN_CITY_LABEL,
)
from database.models.city_service import CityService
from database.models.user_service import UserService

router = Router(name="common")

HELP_TEXT = (
    "🏙️ <b>CITY TYCOON — Help</b>\n\n"
    "/start — register or return to your city\n"
    "/profile — view your stats\n"
    "/city — view your city and districts\n"
    "/business — manage your businesses\n"
    "/inventory — view your items\n"
    "/tasks — view your quests\n"
    "/transactions — recent balance history\n"
    "/rating — leaderboards\n"
    "/events — current events\n"
    "/settings — notification preferences\n"
    "/help — this message\n\n"
    "Use the menu below or tap 🏙️ OPEN CITY to play."
)

_COMING_SOON = {
    "business": ("💼 <b>Business</b>\n\nBusiness management arrives in the next update!"),
    "inventory": ("📦 <b>Inventory</b>\n\nYour inventory is empty for now — coming soon!"),
    "tasks": ("🎯 <b>Quests</b>\n\nDaily and weekly quests are coming soon!"),
    "rating": ("🏆 <b>Leaderboard</b>\n\nLeaderboards are coming soon!"),
    "events": ("🔥 <b>Events</b>\n\nWeekly events are coming soon!"),
}


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(
        "⚙️ <b>Settings</b>\n\nNotification preferences are coming in a future update."
    )


@router.message(Command("city"))
@router.message(F.text == BTN_CITY)
async def city_view(message: Message, session: AsyncSession) -> None:
    """
    Real basic city ownership data (districts owned). The full city view
    — buildings, per-district income, unlock progress — arrives with the
    business/city phase; this shows what's actually in the database now.
    """
    if message.from_user is None:
        return

    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("You haven't started your city yet — send /start first!")
        return

    city = await CityService(session).get_by_user_id(user.id)
    if city is None:
        # Should never happen for a registered user, but don't crash the
        # handler if it somehow does.
        await message.answer("Your city record is missing — try /start again.")
        return

    district_names = CityService.display_names(city)
    districts_text = "\n".join(f"🏘️ {name}" for name in district_names)
    await message.answer(
        f"🏙️ <b>Your City</b>\n\n"
        f"Districts owned ({len(district_names)}):\n{districts_text}\n\n"
        f"Buildings and business management are coming in the next update!"
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
        "🏙️ The Mini App isn't deployed yet in this environment. "
        "Set WEBAPP_URL in .env once it's live (see Phase 3)."
    )
