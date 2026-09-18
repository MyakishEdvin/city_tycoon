"""
🏙 Мой город — дашборд города, меню строительства и колбэки зданий.

Хендлеры только получают действие пользователя и вызывают сервисы
(BuildingService, EconomyService, ProgressionService) — вся игровая
логика и все проверки (деньги, уровень, макс. уровень здания) находятся
там, а не здесь. Callback_data использует схему `namespace:action:arg`,
например `building:build:house`, `building:upgrade:42`.
"""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import BTN_CITY
from database.models.building import PlayerBuilding
from database.models.building_service import BuildingService
from database.models.city import PlayerCity
from database.models.city_service import CityService
from database.models.economy_service import EconomyService
from database.models.user import User
from database.models.user_service import UserService
from game.economy import (
    BUILDING_CATALOG,
    BuildingAlreadyExistsError,
    BuildingLockedError,
    BuildingMaxLevelError,
    BuildingNotFoundError,
    BuildingType,
    InsufficientFundsError,
    InvalidBuildingTypeError,
    building_cost_for_level,
    building_income_for_level,
)
from game.progression import xp_required_for_level

router = Router(name="city")
logger = logging.getLogger("city_tycoon.city")

NOT_STARTED_TEXT = "Вы ещё не начали игру — отправьте /start!"

_BUILDING_ICONS: dict[str, str] = {
    BuildingType.HOUSE.value: "🏠",
    BuildingType.SHOP.value: "🏪",
    BuildingType.FACTORY.value: "🏭",
}


def _money(amount: int) -> str:
    """Формат '$8 450' — с пробелом как разделителем тысяч, как в макете."""
    return f"${amount:,}".replace(",", " ")


def _building_icon(building_type: str) -> str:
    return _BUILDING_ICONS.get(building_type, "🏢")


async def _load_context(telegram_id: int, session: AsyncSession):
    """(user, city, buildings) или None, если игрок ещё не начал игру."""
    user = await UserService(session).get_by_telegram_id(telegram_id)
    if user is None:
        return None
    city = await CityService(session).get_by_user_id(user.id)
    if city is None:
        return None
    buildings = await BuildingService(session).get_buildings(city.id)
    return user, city, buildings


def _dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏗 Построить", callback_data="city:build_menu"),
                InlineKeyboardButton(text="🏢 Мои здания", callback_data="city:buildings"),
            ]
        ]
    )


def _render_dashboard(
    user: User, city: PlayerCity, buildings: list[PlayerBuilding], collected: int
) -> str:
    income_per_hour = EconomyService.income_per_hour(buildings)

    lines: list[str] = ["🏙 <b>CITY TYCOON</b>", ""]
    if collected > 0:
        lines.append(f"💵 Начислено пока вас не было: +{_money(collected)}")
        lines.append("")

    lines += [
        f"👤 Уровень: {user.level}",
        f"⭐ XP: {user.xp} / {xp_required_for_level(user.level)}",
        "",
        f"💰 Баланс: {_money(user.money)}",
        f"📈 Доход: +{_money(income_per_hour)}/час",
        f"👥 Население: {city.population}",
        "",
        f"🏗 Здания: {len(buildings)}",
    ]

    if buildings:
        for building in buildings:
            spec = BUILDING_CATALOG[BuildingType(building.building_type)]
            icon = _building_icon(building.building_type)
            lines.append(f"{icon} {spec.name} Lv.{building.level}")
    else:
        lines.append("Постройте первое здание, чтобы начать зарабатывать!")

    return "\n".join(lines)


async def _show_dashboard(target: Message, telegram_id: int, session: AsyncSession, *, edit: bool) -> None:
    context = await _load_context(telegram_id, session)
    if context is None:
        await target.answer(NOT_STARTED_TEXT)
        return
    user, city, buildings = context

    collected = await EconomyService(session).collect_income(user, city, buildings)
    text = _render_dashboard(user, city, buildings, collected)
    keyboard = _dashboard_keyboard()

    if edit:
        await target.edit_text(text, reply_markup=keyboard)
    else:
        await target.answer(text, reply_markup=keyboard)


@router.message(Command("city"))
@router.message(F.text == BTN_CITY)
async def city_view(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    await _show_dashboard(message, message.from_user.id, session, edit=False)


def _render_build_menu(
    user: User, buildings: list[PlayerBuilding]
) -> tuple[str, InlineKeyboardMarkup]:
    owned_types = {b.building_type for b in buildings}
    lines: list[str] = ["🏗 <b>Постройка</b>", ""]
    rows: list[list[InlineKeyboardButton]] = []

    for building_type, spec in BUILDING_CATALOG.items():
        icon = _building_icon(building_type.value)
        already_built = building_type.value in owned_types
        cost = building_cost_for_level(spec, 1)
        income = building_income_for_level(spec, 1)

        lines.append(f"{icon} <b>{spec.name}</b>")
        lines.append(spec.description)

        if already_built:
            lines.append("✅ Уже построено — улучшайте в разделе «Мои здания»")
        elif user.level < spec.required_player_level:
            lines.append(
                f"🔒 Требуется уровень {spec.required_player_level} "
                f"(у вас {user.level})"
            )
        else:
            lines.append(f"💰 Цена: {_money(cost)}")
            lines.append(f"👥 Население: +{spec.population_bonus}")
            lines.append(f"📈 Доход: {_money(income)}/час")
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Построить: {spec.name}",
                        callback_data=f"building:build:{building_type.value}",
                    )
                ]
            )
        lines.append("")

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="city:show")])
    return "\n".join(lines).rstrip(), InlineKeyboardMarkup(inline_keyboard=rows)


def _render_buildings_list(
    buildings: list[PlayerBuilding],
) -> tuple[str, InlineKeyboardMarkup]:
    if not buildings:
        text = "🏢 <b>Мои здания</b>\n\nУ вас пока нет зданий — постройте первое!"
        rows = [
            [InlineKeyboardButton(text="🏗 Построить", callback_data="city:build_menu")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="city:show")],
        ]
        return text, InlineKeyboardMarkup(inline_keyboard=rows)

    lines = ["🏢 <b>Мои здания</b>", ""]
    rows: list[list[InlineKeyboardButton]] = []
    for building in buildings:
        spec = BUILDING_CATALOG[BuildingType(building.building_type)]
        icon = _building_icon(building.building_type)
        income = building_income_for_level(spec, building.level)

        if building.level >= spec.max_level:
            lines.append(f"{icon} {spec.name} Lv.{building.level} (макс. уровень)")
        else:
            upgrade_cost = building_cost_for_level(spec, building.level + 1)
            lines.append(
                f"{icon} {spec.name} Lv.{building.level} — доход {_money(income)}/час"
            )
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"⬆️ Улучшить: {spec.name} ({_money(upgrade_cost)})",
                        callback_data=f"building:upgrade:{building.id}",
                    )
                ]
            )

    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="city:show")])
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "city:show")
async def cb_city_show(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.message is None:
        return
    await callback.answer()
    await _show_dashboard(callback.message, callback.from_user.id, session, edit=True)


@router.callback_query(F.data == "city:build_menu")
async def cb_build_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.message is None:
        return
    context = await _load_context(callback.from_user.id, session)
    if context is None:
        await callback.answer(NOT_STARTED_TEXT, show_alert=True)
        return
    user, _city, buildings = context
    text, keyboard = _render_build_menu(user, buildings)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "city:buildings")
async def cb_buildings_list(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.message is None:
        return
    context = await _load_context(callback.from_user.id, session)
    if context is None:
        await callback.answer(NOT_STARTED_TEXT, show_alert=True)
        return
    _user, _city, buildings = context
    text, keyboard = _render_buildings_list(buildings)
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=keyboard)


def _error_message(exc: Exception) -> str:
    if isinstance(exc, InsufficientFundsError):
        return f"❌ Недостаточно денег.\n\nНужно: {_money(exc.requested)}\nУ вас: {_money(exc.balance)}"
    if isinstance(exc, BuildingLockedError):
        return (
            f"❌ Это здание пока недоступно.\n\n"
            f"Требуется уровень: {exc.required_level}\n"
            f"Ваш уровень: {exc.player_level}"
        )
    if isinstance(exc, BuildingMaxLevelError):
        return "❌ Максимальный уровень здания уже достигнут."
    if isinstance(exc, BuildingAlreadyExistsError):
        return "❌ Это здание уже построено. Улучшите его в разделе «Мои здания»."
    if isinstance(exc, (BuildingNotFoundError, InvalidBuildingTypeError)):
        return "❌ Здание не найдено."
    logger.warning("Unhandled building action error: %r", exc)
    return "❌ Не удалось выполнить действие. Попробуйте ещё раз."


@router.callback_query(F.data.startswith("building:build:"))
async def cb_build(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return
    building_type = callback.data.removeprefix("building:build:")

    context = await _load_context(callback.from_user.id, session)
    if context is None:
        await callback.answer(NOT_STARTED_TEXT, show_alert=True)
        return
    user, city, _buildings = context

    try:
        building = await BuildingService(session).build(user, city, building_type)
    except Exception as exc:  # noqa: BLE001 — mapped to a friendly message below
        await callback.answer(_error_message(exc), show_alert=True)
        return

    spec = BUILDING_CATALOG[BuildingType(building.building_type)]
    await callback.answer(f"✅ Построено: {spec.name}!")
    await _show_dashboard(callback.message, callback.from_user.id, session, edit=True)


@router.callback_query(F.data.startswith("building:upgrade:"))
async def cb_upgrade(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        return
    try:
        building_id = int(callback.data.removeprefix("building:upgrade:"))
    except ValueError:
        await callback.answer("❌ Здание не найдено.", show_alert=True)
        return

    context = await _load_context(callback.from_user.id, session)
    if context is None:
        await callback.answer(NOT_STARTED_TEXT, show_alert=True)
        return
    user, city, _buildings = context

    try:
        building = await BuildingService(session).upgrade(user, city, building_id)
    except Exception as exc:  # noqa: BLE001 — mapped to a friendly message below
        await callback.answer(_error_message(exc), show_alert=True)
        return

    spec = BUILDING_CATALOG[BuildingType(building.building_type)]
    await callback.answer(f"✅ Улучшено: {spec.name} до Lv.{building.level}!")
    text, keyboard = _render_buildings_list(await BuildingService(session).get_buildings(city.id))
    await callback.message.edit_text(text, reply_markup=keyboard)