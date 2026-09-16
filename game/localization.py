"""
Localization config: the three supported UI languages and mapping from
Telegram's `language_code` (BCP-47, e.g. "uk", "ru", "en-US") to one of
them. Kept separate from game/economy.py since it's not an economy
concern — this is the single source of truth both the backend API and
the bot import.
"""

from __future__ import annotations

SUPPORTED_LANGUAGES: set[str] = {"en", "ru", "uk"}
DEFAULT_LANGUAGE = "en"


def normalize_language_code(language_code: str | None) -> str:
    """
    Map a raw Telegram language_code to one of SUPPORTED_LANGUAGES,
    falling back to DEFAULT_LANGUAGE for anything else (covers None,
    unsupported languages, and regional variants like "en-US" or "ru-RU").
    """
    if not language_code:
        return DEFAULT_LANGUAGE
    primary = language_code.split("-")[0].lower()
    return primary if primary in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE