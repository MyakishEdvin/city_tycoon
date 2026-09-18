"""
/language command.

Lets a player change their stored language preference (the same
`User.language` field the Mini App's Settings screen writes to) directly
from the bot, via an inline keyboard.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user_service import UserService
from game.localization import SUPPORTED_LANGUAGES

router = Router(name="language")

_LANGUAGE_LABELS: dict[str, str] = {
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
}


def _language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_LANGUAGE_LABELS[code], callback_data=f"set_language:{code}"
                )
            ]
            for code in sorted(SUPPORTED_LANGUAGES)
        ]
    )


@router.message(Command("language"))
async def cmd_language(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    user = await UserService(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Вы ещё не начали игру — отправьте /start!")
        return

    current = _LANGUAGE_LABELS.get(user.language, user.language)
    await message.answer(
        f"🌐 Текущий язык: {current}\n\nВыберите новый:",
        reply_markup=_language_keyboard(),
    )


@router.callback_query(F.data.startswith("set_language:"))
async def on_language_selected(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.data is None:
        return

    language = callback.data.removeprefix("set_language:")
    if language not in SUPPORTED_LANGUAGES:
        await callback.answer("Неподдерживаемый язык", show_alert=True)
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Сначала отправьте /start!", show_alert=True)
        return

    await service.set_language(user, language)
    label = _LANGUAGE_LABELS[language]
    await callback.answer(f"Язык изменён на {label}")
    if callback.message is not None:
        await callback.message.edit_text(f"🌐 Язык изменён на {label}")