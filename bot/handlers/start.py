"""
/start handler.

Works identically in private chats and groups: registration is always
keyed by the sending user's telegram_id, never by chat_id. (Per-group
state is its own subsystem, added in a later phase.)
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

    display_name = message.from_user.first_name or message.from_user.username or "Магнат"

    if created:
        text = (
            f"🏙 <b>Добро пожаловать в CITY TYCOON, {display_name}!</b>\n\n"
            f"Вы начинаете с:\n"
            f"💰 <b>${user.money:,}</b>\n"
            f"🏠 небольшой квартирой в Старом городе\n"
            f"⭐ Уровень {user.level}\n\n"
            f"Ваш реферальный код: <code>{user.referral_code}</code>\n"
            f"Поделитесь с друзьями: "
            f"<code>https://t.me/YourBotUsername?start=ref_{user.referral_code}</code>\n\n"
            f"Нажмите <b>🏙 ОТКРЫТЬ ГОРОД</b> ниже, чтобы начать строить свою империю, "
            f"или используйте меню, чтобы посмотреть профиль, бизнес и задания."
        )
    else:
        text = (
            f"👋 С возвращением, {display_name}!\n\n"
            f"💰 Баланс: <b>${user.money:,}</b>\n"
            f"⭐ Уровень {user.level}\n\n"
            f"Нажмите <b>🏙 ОТКРЫТЬ ГОРОД</b>, чтобы продолжить строить, или используйте меню ниже."
        )

    await message.answer(text, reply_markup=build_main_menu())