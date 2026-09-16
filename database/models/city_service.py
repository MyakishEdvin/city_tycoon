"""
CityService: read access to PlayerCity.

Every user is guaranteed a PlayerCity row from the moment they register
(created atomically alongside the User row in UserService.get_or_create),
so this service only needs to read — there's no separate get_or_create
here on purpose, to keep "a user always has exactly one city" a single
invariant enforced in one place.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.city import PlayerCity
from game.economy import DISTRICT_DISPLAY_NAMES, DistrictID


class CityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: int) -> PlayerCity | None:
        result = await self.session.execute(
            select(PlayerCity).where(PlayerCity.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def display_names(city: PlayerCity) -> list[str]:
        names = []
        for district_id in city.unlocked_districts:
            try:
                names.append(DISTRICT_DISPLAY_NAMES[DistrictID(district_id)])
            except ValueError:
                # Unknown district id (e.g. added in a newer version and
                # rolled back) — show it raw rather than failing the view.
                names.append(district_id)
        return names
