from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Main menu button labels.
BTN_CITY = "🏙️ City"
BTN_BUSINESS = "💼 Business"
BTN_INVENTORY = "📦 Inventory"
BTN_QUESTS = "🎯 Quests"
BTN_LEADERBOARD = "🏆 Leaderboard"
BTN_EVENTS = "🔥 Events"
BTN_PROFILE = "👤 Profile"
BTN_BALANCE = "💰 Balance"

# Mini App button.
OPEN_CITY_LABEL = "🏙️ OPEN CITY"


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=OPEN_CITY_LABEL),
            ],
            [
                KeyboardButton(text=BTN_CITY),
                KeyboardButton(text=BTN_BUSINESS),
            ],
            [
                KeyboardButton(text=BTN_INVENTORY),
                KeyboardButton(text=BTN_QUESTS),
            ],
            [
                KeyboardButton(text=BTN_LEADERBOARD),
                KeyboardButton(text=BTN_EVENTS),
            ],
            [
                KeyboardButton(text=BTN_PROFILE),
                KeyboardButton(text=BTN_BALANCE),
            ],
        ],
        resize_keyboard=True,
    )