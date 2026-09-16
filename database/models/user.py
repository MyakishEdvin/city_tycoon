"""
User model.

This table is the root of almost every relationship added in later phases
(businesses, inventory, transactions, quests, companies, ...). Keep it lean:
fields that belong to a specific subsystem (e.g. VIP expiry, notification
prefs) will be added by that subsystem's migration in its own phase rather
than bloating this table upfront.
"""

from __future__ import annotations

import datetime
import secrets

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base
from game.economy import STARTING_BALANCE, STARTING_ENERGY
from game.localization import DEFAULT_LANGUAGE

# Re-exported so existing `from database.models.user import STARTING_BALANCE`
# imports keep working — game/economy.py is now the source of truth.
__all__ = ["User", "STARTING_BALANCE", "STARTING_ENERGY"]


def _generate_referral_code() -> str:
    """8-character, URL-safe, collision-resistant enough for our scale."""
    return secrets.token_hex(4)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    money: Mapped[int] = mapped_column(
        BigInteger, default=STARTING_BALANCE, nullable=False
    )
    reputation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, default=STARTING_ENERGY, nullable=False)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # UI language — one of game.localization.SUPPORTED_LANGUAGES. Set once
    # at registration (from Telegram's language_code when available) and
    # afterwards only ever changed by explicit user action (Settings
    # screen or /language), never overwritten by a later /start.
    language: Mapped[str] = mapped_column(
        String(5), default=DEFAULT_LANGUAGE, nullable=False
    )

    referral_code: Mapped[str] = mapped_column(
        String(16), unique=True, index=True, default=_generate_referral_code, nullable=False
    )
    referred_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referred_by: Mapped["User | None"] = relationship(
        remote_side=[id], foreign_keys=[referred_by_id]
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_active_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Resolved by class name via the shared mapper registry — no direct
    # import needed here, which avoids a user.py <-> city.py/transaction.py
    # circular import. Both modules are imported together in
    # database/models/__init__.py so the names are always registered.
    city: Mapped["PlayerCity | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        # Ordered by id (monotonic on insert), not created_at: two
        # transactions can land in the same second under DB timestamp
        # resolution, which would make created_at ordering ambiguous.
        back_populates="user", order_by="Transaction.id.desc()"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<User id={self.id} telegram_id={self.telegram_id} money={self.money}>"