"""
ProgressionService: the only code path allowed to grant XP or change a
user's level.

No caller (quests, achievements, buildings in later phases) should ever
write to User.xp/User.level directly — they call add_xp() so every XP
source levels a player up through the exact same, testable logic,
including handling a single grant that crosses multiple levels at once
(e.g. a large quest or achievement reward).

Concurrency note: like TransactionService, this mutates a row that could
be written concurrently. It doesn't row-lock yet because nothing calls it
today (no XP-granting endpoint exists until quests/buildings land) — the
first real caller should follow TransactionService's SELECT ... FOR
UPDATE pattern before going live under real concurrent traffic.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User
from game.progression import xp_required_for_level


@dataclass(frozen=True)
class LevelUpResult:
    user: User
    levels_gained: int


class ProgressionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_xp(self, user: User, amount: int) -> LevelUpResult:
        if amount < 0:
            raise ValueError("amount must be >= 0")
        if amount == 0:
            return LevelUpResult(user=user, levels_gained=0)

        user.xp += amount
        levels_gained = 0
        while user.xp >= xp_required_for_level(user.level):
            user.xp -= xp_required_for_level(user.level)
            user.level += 1
            levels_gained += 1

        await self.session.commit()
        await self.session.refresh(user)
        return LevelUpResult(user=user, levels_gained=levels_gained)