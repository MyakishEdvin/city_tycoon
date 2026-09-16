"""
/start handler.

Works identically in private chats and groups: registration is always
keyed by the sending user's telegram_id, never by chat_id. (Per-group
state is its own subsystem, added in Phase 13.)
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import build_main_menu
from database.models.user import STARTING_BALANCE
from database.models.user_service import UserService

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    referral_code = command.args.removeprefix("ref_") if command.args else None

    service = UserService(session)
    user, created = await service.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        referral_code=referral_code,
        language_code=message.from_user.language_code,
    )

    display_name = message.from_user.first_name or message.from_user.username or "Tycoon"

    if created:
        text = (
            f"🏙️ <b>Welcome to CITY TYCOON, {display_name}!</b>\n\n"
            f"You're starting with:\n"
            f"💰 <b>${user.money:,}</b>\n"
            f"🏠 A small apartment in Old Town\n"
            f"⭐ Level {user.level}\n\n"
            f"Your referral code: <code>{user.referral_code}</code>\n"
            f"Share it with friends: "
            f"<code>https://t.me/YourBotUsername?start=ref_{user.referral_code}</code>\n\n"
            f"Tap <b>🏙️ OPEN CITY</b> below to start building your empire, "
            f"or use the menu to check your profile, business, and quests."
        )
    else:
        text = (
            f"👋 Welcome back, {display_name}!\n\n"
            f"💰 Balance: <b>${user.money:,}</b>\n"
            f"⭐ Level {user.level}\n\n"
            f"Tap <b>🏙️ OPEN CITY</b> to keep building, or use the menu below."
        )

    await message.answer(text, reply_markup=build_main_menu())