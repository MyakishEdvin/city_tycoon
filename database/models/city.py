"""
PlayerCity model.

Deliberately minimal: this is the "basic city ownership data" requested
now — which districts a player owns — not the full city/business system
(buildings, income, per-district stats), which lands with the business
phase. Every user gets exactly one row, created at registration.
"""

from __future__ import annotations

import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base
from game.economy import DEFAULT_UNLOCKED_DISTRICTS, STARTING_POPULATION


class PlayerCity(Base):
    __tablename__ = "player_cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="city")  # noqa: F821

    # List of game.economy.DistrictID values this player has unlocked.
    # Stored as JSON (not a Postgres ARRAY) so it also works against the
    # SQLite database used in tests, and so the business phase can freely
    # change what "unlocked" means without a column migration.
    unlocked_districts: Mapped[list[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # City-level stat (not identity, so it lives here rather than on
    # User). Grown by houses/shops/factories at construction time (see
    # game.economy.BuildingSpec.population_bonus).
    population: Mapped[int] = mapped_column(
        Integer, default=STARTING_POPULATION, nullable=False
    )

    # Anchor for on-demand passive income calculation (EconomyService):
    # accumulated income = income_per_hour * hours since this timestamp,
    # capped at MAX_OFFLINE_INCOME_HOURS. No background worker needed —
    # this is advanced to "now" every time income is collected.
    last_income_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    buildings: Mapped[list["PlayerBuilding"]] = relationship(  # noqa: F821
        back_populates="city", cascade="all, delete-orphan", order_by="PlayerBuilding.id"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<PlayerCity user_id={self.user_id} districts={self.unlocked_districts}>"


def build_starting_city(user_id: int) -> PlayerCity:
    """Factory for the city row created alongside a brand-new user."""
    return PlayerCity(
        user_id=user_id,
        unlocked_districts=list(DEFAULT_UNLOCKED_DISTRICTS),
        population=STARTING_POPULATION,
    )
