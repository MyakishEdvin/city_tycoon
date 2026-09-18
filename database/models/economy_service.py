"""
EconomyService: income-per-hour calculation and on-demand passive-income
collection.

No background worker runs per player. Instead, PlayerCity.last_income_at
anchors a lazy calculation: whenever the player opens their city (or any
handler/endpoint calls collect_income), we compute elapsed time since the
last collection, credit the corresponding income through
TransactionService (so it's a normal, audited transaction), and advance
last_income_at to now. Accumulation is capped at MAX_OFFLINE_INCOME_HOURS
so long absences don't generate unbounded money.
"""

from __future__ import annotations

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.building import PlayerBuilding
from database.models.city import PlayerCity
from database.models.transaction_service import TransactionService
from database.models.user import User
from game.economy import (
    BUILDING_CATALOG,
    MAX_OFFLINE_INCOME_HOURS,
    BuildingType,
    TransactionType,
    building_income_for_level,
)


class EconomyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def income_per_hour(buildings: list[PlayerBuilding]) -> int:
        """Total city income/hour from all buildings at their current level."""
        total = 0
        for building in buildings:
            spec = BUILDING_CATALOG[BuildingType(building.building_type)]
            total += building_income_for_level(spec, building.level)
        return total

    async def collect_income(
        self, user: User, city: PlayerCity, buildings: list[PlayerBuilding]
    ) -> int:
        """
        Credit accumulated passive income since `city.last_income_at` and
        advance the anchor to now. Returns the amount credited (0 if none
        — e.g. no buildings yet, or called again moments later).

        Deliberately a no-op (no DB write at all) when amount is 0: if we
        advanced last_income_at on every call regardless, frequent calls
        (opening the city repeatedly) would keep resetting the window
        before any fractional income ever accumulates past int()
        truncation, and the player would never actually get paid.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        last_income_at = city.last_income_at
        if last_income_at.tzinfo is None:
            # SQLite (used in tests) round-trips DateTime(timezone=True)
            # as naive — it has no native tz-aware timestamp type, unlike
            # PostgreSQL/asyncpg in production, which always returns this
            # as tz-aware. We only ever write UTC into this column, so
            # treating a naive read as UTC is correct in both cases.
            last_income_at = last_income_at.replace(tzinfo=datetime.timezone.utc)
        elapsed_seconds = max(0.0, (now - last_income_at).total_seconds())
        elapsed_hours = min(elapsed_seconds / 3600, MAX_OFFLINE_INCOME_HOURS)

        income_per_hour = self.income_per_hour(buildings)
        amount = int(income_per_hour * elapsed_hours)

        if amount <= 0:
            return 0

        # Advance the anchor to `now` *before* crediting so both land in
        # TransactionService's single commit — never money credited
        # without the anchor moving (which would let the same window be
        # collected twice), and never the reverse.
        city.last_income_at = now
        await TransactionService(self.session).apply_delta(
            user_id=user.id, delta=amount, tx_type=TransactionType.BUILDING_INCOME
        )
        await self.session.refresh(city)
        return amount