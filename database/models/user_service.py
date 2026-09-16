"""
UserService: the only code path allowed to create or fetch User rows.

Centralizing this now (rather than letting handlers do `session.add(User(...))`
directly) means every later phase — the FastAPI backend, background jobs,
admin tools — reuses the exact same registration/lookup logic, so behavior
like "idempotent /start" and "referral resolution" can't drift between
entry points.
"""

from __future__ import annotations

import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.city import build_starting_city
from database.models.transaction import Transaction
from database.models.user import User
from game.economy import STARTING_BALANCE, TransactionType
from game.localization import SUPPORTED_LANGUAGES, normalize_language_code

logger = logging.getLogger("city_tycoon.user_service")


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, referral_code: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.referral_code == referral_code)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        referral_code: str | None = None,
        language_code: str | None = None,
    ) -> tuple[User, bool]:
        """
        Fetch the user for this telegram_id, creating it if it doesn't
        exist yet. Returns (user, created).

        This must be idempotent: Telegram can and does redeliver updates,
        and a user can tap /start multiple times. Re-running this should
        never reset progress or create a duplicate row. Uniqueness is
        enforced at the database level via the unique index on
        telegram_id, so even a race between two concurrent /start
        updates for the same user cannot create two rows.

        `language_code` (Telegram's raw language_code, e.g. "uk", "en-US")
        is only used to seed the language on first registration — it is
        never applied to an existing user, since language is a sticky
        user preference from that point on (see set_language).
        """
        existing = await self.get_by_telegram_id(telegram_id)
        if existing is not None:
            # Keep denormalized profile fields fresh, and record activity,
            # but never touch progression fields (money, level, xp, ...)
            # or the user's chosen language.
            existing.username = username
            existing.first_name = first_name
            existing.last_active_at = datetime.datetime.now(datetime.timezone.utc)
            await self.session.commit()
            return existing, False

        referred_by: User | None = None
        if referral_code:
            referred_by = await self.get_by_referral_code(referral_code)
            if referred_by is not None and referred_by.telegram_id == telegram_id:
                # Guard against a user somehow referring themselves.
                referred_by = None

        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referred_by_id=referred_by.id if referred_by else None,
            language=normalize_language_code(language_code),
        )
        self.session.add(new_user)
        try:
            # Flush (not commit) to obtain new_user.id for the FK below,
            # while keeping the user row, its starting city, and its
            # starting-balance audit transaction in one atomic commit.
            await self.session.flush()

            self.session.add(build_starting_city(new_user.id))
            self.session.add(
                Transaction(
                    user_id=new_user.id,
                    type=TransactionType.STARTING_BALANCE.value,
                    amount=STARTING_BALANCE,
                    balance_before=0,
                    balance_after=STARTING_BALANCE,
                    reference_id=f"starting_balance:{telegram_id}",
                )
            )
            await self.session.commit()
        except Exception:
            # Handles the rare race where two concurrent /start requests
            # for the same brand-new telegram_id both pass the SELECT
            # check above before either commits. The unique constraint on
            # telegram_id makes the second commit fail; we roll back and
            # return the row the other request created instead of erroring.
            await self.session.rollback()
            logger.warning(
                "Race on user creation for telegram_id=%s, refetching", telegram_id
            )
            existing = await self.get_by_telegram_id(telegram_id)
            if existing is not None:
                return existing, False
            raise

        await self.session.refresh(new_user)
        logger.info(
            "New player registered: telegram_id=%s referred_by=%s",
            telegram_id,
            referred_by.id if referred_by else None,
        )
        return new_user, True

    async def touch_activity(self, user: User) -> None:
        user.last_active_at = datetime.datetime.now(datetime.timezone.utc)
        await self.session.commit()

    async def set_language(self, user: User, language: str) -> User:
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")
        user.language = language
        await self.session.commit()
        await self.session.refresh(user)
        return user