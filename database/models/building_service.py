"""
BuildingService: the only code path allowed to construct or upgrade a
building.

Atomicity note (important): TransactionService.apply_delta() performs
its own SELECT ... FOR UPDATE + commit as a self-contained unit. Rather
than duplicating that logic, this service stages the building/population
change on the session first (session.add / attribute mutation, not yet
committed) and then calls apply_delta() last. Since a SQLAlchemy session
commits *everything* pending — not just the caller's own objects — the
money debit and the building change land in exactly one transaction:
  * insufficient funds -> apply_delta rolls back -> the staged building/
    population change is discarded too (never "building created but
    money not charged").
  * success -> apply_delta commits -> money and building change persist
    together (never "money charged but no building").
This also means concurrent build/upgrade attempts by the same player
safely serialize on the same user-row lock apply_delta already takes.

XP is granted via ProgressionService *after* that commit succeeds. It is
technically a second, separate commit — acceptable here since the only
strict atomicity requirement is money-vs-building-state; a rare failure
between the two would just mean a missed XP grant, not a duplicated or
lost purchase.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.building import PlayerBuilding
from database.models.city import PlayerCity
from database.models.progression_service import ProgressionService
from database.models.transaction_service import TransactionService
from database.models.user import User
from game.economy import (
    BUILD_XP_REWARD,
    BUILDING_CATALOG,
    UPGRADE_XP_REWARD,
    BuildingAlreadyExistsError,
    BuildingLockedError,
    BuildingMaxLevelError,
    BuildingNotFoundError,
    BuildingSpec,
    BuildingType,
    InvalidBuildingTypeError,
    TransactionType,
    building_cost_for_level,
)


def _spec_for(building_type: str) -> BuildingSpec:
    try:
        return BUILDING_CATALOG[BuildingType(building_type)]
    except ValueError:
        raise InvalidBuildingTypeError(building_type) from None


class BuildingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_buildings(self, city_id: int) -> list[PlayerBuilding]:
        result = await self.session.execute(
            select(PlayerBuilding)
            .where(PlayerBuilding.city_id == city_id)
            .order_by(PlayerBuilding.id)
        )
        return list(result.scalars().all())

    async def get_building(self, city_id: int, building_id: int) -> PlayerBuilding | None:
        building = await self.session.get(PlayerBuilding, building_id)
        if building is None or building.city_id != city_id:
            return None
        return building

    async def get_building_by_type(
        self, city_id: int, building_type: str
    ) -> PlayerBuilding | None:
        result = await self.session.execute(
            select(PlayerBuilding).where(
                PlayerBuilding.city_id == city_id,
                PlayerBuilding.building_type == building_type,
            )
        )
        return result.scalar_one_or_none()

    async def build(self, user: User, city: PlayerCity, building_type: str) -> PlayerBuilding:
        spec = _spec_for(building_type)

        if user.level < spec.required_player_level:
            raise BuildingLockedError(building_type, spec.required_player_level, user.level)

        # One building per type per city (matches the dashboard: "🏠 Жилой
        # дом Lv.2" — a single upgradeable instance, not stackable copies).
        existing = await self.get_building_by_type(city.id, building_type)
        if existing is not None:
            raise BuildingAlreadyExistsError(building_type)

        cost = building_cost_for_level(spec, 1)

        building = PlayerBuilding(city_id=city.id, building_type=building_type, level=1)
        self.session.add(building)
        city.population += spec.population_bonus

        try:
            # Commits `building`, the population change, and the debit
            # together — or rolls all of it back on insufficient funds.
            # See module docstring.
            await TransactionService(self.session).apply_delta(
                user_id=user.id, delta=-cost, tx_type=TransactionType.BUILDING_PURCHASE
            )
        except Exception:
            # apply_delta's rollback expires `city` (it was dirtied here,
            # above) and expunges the never-flushed `building`. Refresh
            # `city` back to its true persisted state so the caller can
            # keep using the same object safely — otherwise touching
            # city.* after catching this exception raises MissingGreenlet
            # (expired-attribute access outside an active async/greenlet
            # context). TransactionService only knows about `user`; it
            # can't do this for us.
            await self.session.refresh(city)
            raise

        await self.session.refresh(building)
        await self.session.refresh(city)

        await ProgressionService(self.session).add_xp(user, BUILD_XP_REWARD)
        return building

    async def upgrade(self, user: User, city: PlayerCity, building_id: int) -> PlayerBuilding:
        building = await self.get_building(city.id, building_id)
        if building is None:
            raise BuildingNotFoundError(building_id)

        spec = _spec_for(building.building_type)
        if building.level >= spec.max_level:
            raise BuildingMaxLevelError(building.building_type, spec.max_level)

        cost = building_cost_for_level(spec, building.level + 1)
        building.level += 1

        try:
            await TransactionService(self.session).apply_delta(
                user_id=user.id, delta=-cost, tx_type=TransactionType.BUILDING_UPGRADE
            )
        except Exception:
            # session.rollback() conservatively expires every object in
            # the session's identity map, not just the ones this method
            # dirtied — so `city` needs refreshing here too, even though
            # upgrade() itself never mutates it, or `city.id` access
            # right after catching this exception can also raise
            # MissingGreenlet.
            await self.session.refresh(building)
            await self.session.refresh(city)
            raise
        await self.session.refresh(building)

        await ProgressionService(self.session).add_xp(user, UPGRADE_XP_REWARD)
        return building