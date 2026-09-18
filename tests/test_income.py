from __future__ import annotations

import datetime

from database.models.building_service import BuildingService
from database.models.city_service import CityService
from database.models.economy_service import EconomyService
from database.models.transaction_service import TransactionService
from database.models.user_service import UserService
from game.economy import (
    BUILDING_CATALOG,
    MAX_OFFLINE_INCOME_HOURS,
    STARTING_BALANCE,
    BuildingType,
    TransactionType,
    building_income_for_level,
)


async def _make_player_with_house(session, telegram_id: int):
    user, _ = await UserService(session).get_or_create(
        telegram_id=telegram_id, username=f"user{telegram_id}", first_name="Player"
    )
    city = await CityService(session).get_by_user_id(user.id)
    building = await BuildingService(session).build(user, city, BuildingType.HOUSE.value)
    return user, city, building


async def test_income_per_hour_sums_all_buildings(session):
    user, city, _house = await _make_player_with_house(session, 5001)
    user.level = 2
    await session.commit()
    
    await TransactionService(session).apply_delta(
    user_id=user.id,
    delta=1000,
    tx_type=TransactionType.ADMIN_CREDIT,
)
    await BuildingService(session).build(user, city, BuildingType.SHOP.value)

    buildings = await BuildingService(session).get_buildings(city.id)
    expected = sum(
        building_income_for_level(BUILDING_CATALOG[BuildingType(b.building_type)], b.level)
        for b in buildings
    )
    assert EconomyService.income_per_hour(buildings) == expected
    assert expected > 0


async def test_collect_income_credits_accumulated_amount(session):
    user, city, _house = await _make_player_with_house(session, 5002)
    buildings = await BuildingService(session).get_buildings(city.id)
    income_per_hour = EconomyService.income_per_hour(buildings)

    # Simulate exactly one hour having passed since the last collection.
    city.last_income_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=1
    )
    await session.commit()

    balance_before = user.money
    collected = await EconomyService(session).collect_income(user, city, buildings)

    assert collected == income_per_hour
    await session.refresh(user)
    assert user.money == balance_before + income_per_hour

    history = await TransactionService(session).get_history(user.id, limit=1)
    assert history[0].type == TransactionType.BUILDING_INCOME.value
    assert history[0].amount == income_per_hour


async def test_collect_income_is_capped_for_long_absences(session):
    user, city, _house = await _make_player_with_house(session, 5003)
    buildings = await BuildingService(session).get_buildings(city.id)
    income_per_hour = EconomyService.income_per_hour(buildings)

    # Simulate 100 hours offline — far beyond the cap.
    city.last_income_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=100
    )
    await session.commit()

    collected = await EconomyService(session).collect_income(user, city, buildings)

    assert collected == income_per_hour * MAX_OFFLINE_INCOME_HOURS


async def test_collecting_twice_in_a_row_does_not_double_pay(session):
    user, city, _house = await _make_player_with_house(session, 5004)
    buildings = await BuildingService(session).get_buildings(city.id)

    city.last_income_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=1
    )
    await session.commit()

    first = await EconomyService(session).collect_income(user, city, buildings)
    second = await EconomyService(session).collect_income(user, city, buildings)

    assert first > 0
    assert second == 0


async def test_collect_income_with_no_buildings_is_a_no_op(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=5005, username="empty", first_name="Empty"
    )
    city = await CityService(session).get_by_user_id(user.id)
    original_anchor = city.last_income_at

    collected = await EconomyService(session).collect_income(user, city, [])

    assert collected == 0
    assert user.money == STARTING_BALANCE
    # The anchor must not advance on a no-op collection, or a player
    # opening their city repeatedly before building anything would keep
    # resetting the window and could never accumulate real income later.
    assert city.last_income_at == original_anchor