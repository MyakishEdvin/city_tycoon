"""
Telegram WebApp initData validation.

Per Telegram's official Mini App auth spec: the frontend sends the raw
`initData` string it received from `window.Telegram.WebApp.initData`,
untouched. This module verifies its HMAC-SHA256 signature against the
bot token and extracts the Telegram user it certifies. This is the ONLY
way the backend learns who is calling it — a client-supplied user id in
a body or query param is never trusted anywhere in this API.

Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from bot.config import settings

# How long a given initData payload is accepted after Telegram issued it.
# Telegram reissues initData each time the Mini App is opened, so this
# only needs to cover a single session's realistic lifetime.
INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class TelegramWebAppUser:
    """The authenticated Telegram identity for the current request."""

    id: int
    username: str | None
    first_name: str | None
    language_code: str | None


def validate_init_data(init_data: str, bot_token: str) -> dict[str, str]:
    """
    Verify initData's signature and freshness. Returns the parsed
    key/value pairs on success. Raises ValueError on any failure —
    callers must treat that as "unauthenticated", not log the reason to
    the client.
    """
    if not init_data:
        raise ValueError("empty init data")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("missing hash")

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("signature mismatch")

    try:
        auth_date = int(parsed.get("auth_date", "0"))
    except ValueError as exc:
        raise ValueError("invalid auth_date") from exc

    if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        raise ValueError("init data expired")

    return parsed


def _extract_user(parsed: dict[str, str]) -> TelegramWebAppUser:
    raw_user = parsed.get("user")
    if not raw_user:
        raise ValueError("init data missing user")
    try:
        payload = json.loads(raw_user)
        return TelegramWebAppUser(
            id=int(payload["id"]),
            username=payload.get("username"),
            first_name=payload.get("first_name"),
            language_code=payload.get("language_code"),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError("malformed user field") from exc


async def get_current_telegram_user(
    authorization: str | None = Header(default=None),
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
) -> TelegramWebAppUser:
    """
    FastAPI dependency: validates initData from either the
    `Authorization: tma <initData>` header (Telegram's documented scheme)
    or the `X-Telegram-Init-Data` header, and returns the certified user.
    Raises 401 on anything invalid or missing.
    """
    init_data: str | None = None
    if authorization and authorization.startswith("tma "):
        init_data = authorization[len("tma "):]
    elif x_telegram_init_data:
        init_data = x_telegram_init_data

    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Telegram init data",
        )

    try:
        parsed = validate_init_data(init_data, settings.BOT_TOKEN)
        return _extract_user(parsed)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram init data",
        )