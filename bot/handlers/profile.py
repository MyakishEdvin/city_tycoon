"""
/profile command and the "👤 Profile" keyboard button.

Income-per-hour, achievements, and inventory counts are wired in once
businesses (Phase 2) and inventory (Phase 9) exist. For now this shows
everything the User model currently tracks.
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


def _format_profile(user, display_name: str, district_count: int) -> str:
    username_line = f"@{user.username}" if user.username else display_name
    return (
        f"👤 <b>{username_line}</b>\n\n"
        f"⭐ Level {user.level} ({user.xp} XP)\n"
        f"💰 ${user.money:,}\n"
        f"🏆 Reputation: {user.reputation}\n"
        f"⚡ Energy: {user.energy}\n"
        f"🔥 Streak: {user.daily_streak} days\n"
        f"🏙️ Districts owned: {district_count}\n\n"
        f"🔗 Referral code: <code>{user.referral_code}</code>\n"
        f"📅 Playing since: {user.created_at:%Y-%m-%d}"
    )


def _format_transaction_line(tx: Transaction) -> str:
    sign = "+" if tx.amount >= 0 else "-"
    label = tx.type.replace("_", " ").title()
    return f"{sign}${abs(tx.amount):,} — {label} ({tx.created_at:%b %d, %H:%M})"


async def _send_profile(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(message.from_user.id)

    if user is None:
        await message.answer("You haven't started your city yet — send /start first!")
        return

    await service.touch_activity(user)
    city = await CityService(session).get_by_user_id(user.id)
    district_count = len(city.unlocked_districts) if city else 0
    display_name = message.from_user.first_name or message.from_user.username or "Tycoon"
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
        await message.answer("You haven't started your city yet — send /start first!")
        return

    await service.touch_activity(user)

    transactions = await TransactionService(session).get_history(
        user.id, limit=RECENT_TRANSACTIONS_SHOWN
    )

    # Income-per-hour is added once businesses exist in Phase 2.
    lines = [f"💰 Balance: <b>${user.money:,}</b>"]
    if transactions:
        lines.append("\n📜 <b>Recent transactions</b>")
        lines.extend(_format_transaction_line(tx) for tx in transactions)
    await message.answer("\n".join(lines))


@router.message(Command("transactions"))
async def cmd_transactions(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return

    service = UserService(session)
    user = await service.get_by_telegram_id(message.from_user.id)
    if user is None:
        await message.answer("You haven't started your city yet — send /start first!")
        return

    await service.touch_activity(user)
    transactions = await TransactionService(session).get_history(user.id, limit=20)

    if not transactions:
        await message.answer("No transactions yet.")
        return

    lines = ["📜 <b>Transaction history</b>\n"]
    lines.extend(_format_transaction_line(tx) for tx in transactions)
    await message.answer("\n".join(lines))
