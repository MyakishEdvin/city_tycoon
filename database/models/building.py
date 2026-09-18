"""
PlayerBuilding model.

Every constructed building is a row here, owned by a PlayerCity. Kept
deliberately generic (type + level) rather than one table per building
type — game.economy.BUILDING_CATALOG holds the per-type stats, so adding
a new building type later is a catalog entry, not a migration.
"""

from __future__ import annotations

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class PlayerBuilding(Base):
    __tablename__ = "player_buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    city_id: Mapped[int] = mapped_column(
        ForeignKey("player_cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city: Mapped["PlayerCity"] = relationship(back_populates="buildings")  # noqa: F821

    # One of game.economy.BuildingType. Stored as text (not a native SQL
    # enum) for the same reason as Transaction.type — new building types
    # shouldn't need an ALTER TYPE migration.
    building_type: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return f"<PlayerBuilding id={self.id} type={self.building_type} level={self.level}>"