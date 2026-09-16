"""
Main reply keyboard shown after /start.

The "OPEN CITY" button launches the Telegram Mini App via a WebApp button
when WEBAPP_URL is configured (Phase 3 onward). Telegram requires WebApp
buttons to point at a real HTTPS URL, so until the Mini App is deployed we
fall back to a plain text button; common.py replies with a friendly
"coming soon" message when it's tapped in that state.
"""

from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from bot.config import settings

OPEN_CITY_LABEL = "🏙️ OPEN CITY"

BTN_CITY = "🏙️ City"
BTN_BUSINESS = "💼 Business"
BTN_BALANCE = "💰 Balance"
BTN_INVENTORY = "📦 Inventory"
BTN_QUESTS = "🎯 Quests"
BTN_LEADERBOARD = "🏆 Leaderboard"
BTN_EVENTS = "🔥 Events"
BTN_PROFILE = "👤 Profile"


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
