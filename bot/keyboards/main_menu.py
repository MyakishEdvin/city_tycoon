"""
Main reply keyboard shown after /start.

The "OPEN CITY" button launches the Telegram Mini App via a WebApp button
when WEBAPP_URL is configured. Telegram requires WebApp buttons to point
at a real HTTPS URL, so until the Mini App is deployed we fall back to a
plain text button; common.py replies with a friendly "coming soon"
message when it's tapped in that state.
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot.config import settings

OPEN_CITY_LABEL = "🏙 ОТКРЫТЬ ГОРОД"

BTN_CITY = "🏙 Мой город"
BTN_BUSINESS = "💼 Бизнес"
BTN_BALANCE = "💰 Баланс"
BTN_INVENTORY = "📦 Инвентарь"
BTN_QUESTS = "🎯 Задания"
BTN_LEADERBOARD = "🏆 Рейтинг"
BTN_EVENTS = "🔥 События"
BTN_PROFILE = "👤 Профиль"


def build_main_menu() -> ReplyKeyboardMarkup:
    if settings.webapp_configured:
        open_city_button = KeyboardButton(
            text=OPEN_CITY_LABEL,
            web_app=WebAppInfo(url=settings.WEBAPP_URL),
        )
    else:
        open_city_button = KeyboardButton(text=OPEN_CITY_LABEL)

    return ReplyKeyboardMarkup(
        keyboard=[
            [open_city_button],
            [KeyboardButton(text=BTN_CITY), KeyboardButton(text=BTN_BUSINESS)],
            [KeyboardButton(text=BTN_BALANCE), KeyboardButton(text=BTN_INVENTORY)],
            [KeyboardButton(text=BTN_QUESTS), KeyboardButton(text=BTN_LEADERBOARD)],
            [KeyboardButton(text=BTN_EVENTS), KeyboardButton(text=BTN_PROFILE)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )