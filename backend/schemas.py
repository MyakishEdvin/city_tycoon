from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class CityOut(BaseModel):
    unlocked_districts: list[str]
    population: int
    # Always 0 until the building system (next phase) adds a buildings
    # table — this is an honest current count, not a placeholder value.
    building_count: int


class MeResponse(BaseModel):
    telegram_id: int
    username: str | None
    first_name: str | None
    level: int
    xp: int
    xp_for_next_level: int
    level_progress: float
    money: int
    reputation: int
    energy: int
    daily_streak: int
    language: str
    referral_code: str
    city: CityOut


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount: int
    balance_before: int
    balance_after: int
    reference_id: str | None
    created_at: datetime.datetime


class TransactionHistoryResponse(BaseModel):
    items: list[TransactionOut]
    limit: int
    offset: int


class LanguageUpdateRequest(BaseModel):
    language: str