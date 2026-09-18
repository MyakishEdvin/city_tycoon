"""
/profile command and the "👤 Профиль" keyboard button.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import BTN_BALANCE, BTN_PROFILE
from database.models.city_service import CityService
from database.models.transaction import Transaction
from database.models.transaction_service import TransactionService
from database.models.user_service import UserService

router = Router(name="profile")

RECENT_TRANSACTIONS_SHOWN = 5

_TRANSACTION_LABELS: dict[str, str] = {
    "starting_balance": "Стартовый баланс",
    "admin_credit": "Начисление",
    "admin_debit": "Списание",
    "building_purchase": "Постройка здания",
    "building_upgrade": "Улучшение здания",
    "building_income": "Доход от зданий",
}


def _format_profile(user, display_name: str, district_count: int) -> str:
    username_line = f"@{user.username}" if user.username else display_name
    return (
        f"👤 <b>{username_line}</b>\n\n"
        f"⭐ Уровень {user.level} ({user.xp} XP)\n"
        f"💰 ${user.money:,}\n"
        f"🏆 Репутация: {user.reputation}\n"
        f"⚡ Энергия: {user.energy}\n"
        f"🔥 Серия входов: {user.daily_streak} дн.\n"
        f"🏙 Районов открыто: {district_count}\n\n"
        f"🔗 Реферальный код: <code>{user.referral_code}</code>\n"
        f"📅 В игре с: {user.created_at:%Y-%m-%d}"
    )


def _format_transaction_line(tx: Transaction) -> str:
    sign = "+" if tx.amount >= 0 else "-"
    label = _TRANSACTION_LABELS.get(tx.type, tx.type.replace("_", " "))
    return f"{sign}${abs(tx.amount):,} — {label} ({tx.created_at:%d.%m, %H:%M})"


async def _send_profile(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(message.from_user.id)

    if user is None:
        await message.answer("Вы ещё не начали игру — отправьте /start!")
        return

    await service.touch_activity(user)
    city = await CityService(session).get_by_user_id(user.id)
    district_count = len(city.unlocked_districts) if city else 0
    display_name = message.from_user.first_name or message.from_user.username or "Магнат"
    await message.answer(_format_profile(user, display_name, district_count))


@router.message(Command("profile"))
async def cmd_profile(message: Message, session: AsyncSession) -> None:
    await _send_profile(message, session)


@router.message(F.text == BTN_PROFILE)
async def btn_profile(message: Message, session: AsyncSession) -> None:
    await _send_profile(message, session)


@router.message(F.text == BTN_BALANCE)
async def btn_balance(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(message.from_user.id)

    if user is None:
        await message.answer("Вы ещё не начали игру — отправьте /start!")
        return

    await service.touch_activity(user)

    transactions = await TransactionService(session).get_history(
        user.id, limit=RECENT_TRANSACTIONS_SHOWN
    )

    lines = [f"💰 Баланс: <b>${user.money:,}</b>"]
    if transactions:
        lines.append("\n📜 <b>Последние операции</b>")
        lines.extend(_format_transaction_line(tx) for tx in transactions)
    await message.answer("\n".join(lines))


@router.message(Command("transactions"))
async def cmd_transactions(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("Вы ещё не начали игру — отправьте /start!")
        return

    await service.touch_activity(user)
    transactions = await TransactionService(session).get_history(user.id, limit=20)

    if not transactions:
        await message.answer("Операций пока нет.")
        return

    lines = ["📜 <b>История операций</b>\n"]
    lines.extend(_format_transaction_line(tx) for tx in transactions)
    await message.answer("\n".join(lines))
