from __future__ import annotations

import pytest

from database.models.building import PlayerBuilding
from database.models.building_service import BuildingService
from database.models.city_service import CityService
from database.models.user_service import UserService
from game.economy import (
    BUILDING_CATALOG,
    STARTING_BALANCE,
    STARTING_POPULATION,
    BuildingAlreadyExistsError,
    BuildingLockedError,
    BuildingMaxLevelError,
    BuildingNotFoundError,
    BuildingType,
    InsufficientFundsError,
    building_cost_for_level,
)


async def _make_player(session, telegram_id: int):
    user, _ = await UserService(session).get_or_create(
        telegram_id=telegram_id, username=f"user{telegram_id}", first_name="Player"
    )
    city = await CityService(session).get_by_user_id(user.id)
    return user, city


async def test_build_house_succeeds_with_sufficient_balance(session):
    user, city = await _make_player(session, 4001)
    service = BuildingService(session)

    house_cost = building_cost_for_level(BUILDING_CATALOG[BuildingType.HOUSE], 1)
    assert house_cost <= STARTING_BALANCE  # sanity: affordable at game start

    building = await service.build(user, city, BuildingType.HOUSE.value)

    assert building.id is not None
    assert building.building_type == BuildingType.HOUSE.value
    assert building.level == 1

    await session.refresh(user)
    assert user.money == STARTING_BALANCE - house_cost


async def test_build_fails_with_insufficient_balance(session):
    user, city = await _make_player(session, 4002)
    service = BuildingService(session)

    # Factory costs far more than the starting balance and requires
    # level 3 — bump the player's level first so we're testing the
    # money check specifically, not the level lock.
    user.level = 3
    await session.commit()

    with pytest.raises(InsufficientFundsError):
        await service.build(user, city, BuildingType.FACTORY.value)

    await session.refresh(user)
    assert user.money == STARTING_BALANCE

    buildings = await service.get_buildings(city.id)
    assert buildings == []


async def test_build_fails_when_player_level_too_low(session):
    user, city = await _make_player(session, 4003)
    service = BuildingService(session)

    with pytest.raises(BuildingLockedError):
        await service.build(user, city, BuildingType.SHOP.value)  # requires level 2

    await session.refresh(user)
    assert user.money == STARTING_BALANCE


async def test_build_house_increases_population(session):
    user, city = await _make_player(session, 4004)
    service = BuildingService(session)
    spec = BUILDING_CATALOG[BuildingType.HOUSE]

    await service.build(user, city, BuildingType.HOUSE.value)

    await session.refresh(city)
    assert city.population == STARTING_POPULATION + spec.population_bonus


async def test_cannot_build_same_type_twice(session):
    user, city = await _make_player(session, 4005)
    service = BuildingService(session)

    await service.build(user, city, BuildingType.HOUSE.value)

    with pytest.raises(BuildingAlreadyExistsError):
        await service.build(user, city, BuildingType.HOUSE.value)


async def test_build_grants_xp(session):
    from game.economy import BUILD_XP_REWARD

    user, city = await _make_player(session, 4006)
    service = BuildingService(session)

    await service.build(user, city, BuildingType.HOUSE.value)

    await session.refresh(user)
    assert user.xp == BUILD_XP_REWARD


async def test_upgrade_increases_level_and_charges_cost(session):
    user, city = await _make_player(session, 4007)
    service = BuildingService(session)
    spec = BUILDING_CATALOG[BuildingType.HOUSE]

    building = await service.build(user, city, BuildingType.HOUSE.value)
    balance_after_build = (await UserService(session).get_by_telegram_id(4007)).money

    upgraded = await service.upgrade(user, city, building.id)

    assert upgraded.level == 2
    upgrade_cost = building_cost_for_level(spec, 2)

    await session.refresh(user)
    assert user.money == balance_after_build - upgrade_cost


async def test_upgrade_grants_xp(session):
    from game.economy import BUILD_XP_REWARD, UPGRADE_XP_REWARD

    user, city = await _make_player(session, 4008)
    service = BuildingService(session)

    building = await service.build(user, city, BuildingType.HOUSE.value)
    await service.upgrade(user, city, building.id)

    await session.refresh(user)
    assert user.xp == BUILD_XP_REWARD + UPGRADE_XP_REWARD


async def test_cannot_upgrade_past_max_level(session):
    user, city = await _make_player(session, 4009)
    service = BuildingService(session)
    spec = BUILDING_CATALOG[BuildingType.HOUSE]

    # Give the player effectively unlimited money so we can reach max
    # level without hitting InsufficientFundsError first.
    user.money = 10_000_000
    await session.commit()

    building = await service.build(user, city, BuildingType.HOUSE.value)
    for _ in range(spec.max_level - 1):
        building = await service.upgrade(user, city, building.id)

    assert building.level == spec.max_level

    with pytest.raises(BuildingMaxLevelError):
        await service.upgrade(user, city, building.id)


async def test_upgrade_unknown_building_raises_not_found(session):
    user, city = await _make_player(session, 4010)
    service = BuildingService(session)

    with pytest.raises(BuildingNotFoundError):
        await service.upgrade(user, city, 999999)


async def test_upgrade_insufficient_funds_does_not_change_level(session):
    user, city = await _make_player(session, 4011)
    service = BuildingService(session)

    building = await service.build(user, city, BuildingType.HOUSE.value)
    # Drain the balance so the upgrade can't be afforded.
    user.money = 0
    await session.commit()

    with pytest.raises(InsufficientFundsError):
        await service.upgrade(user, city, building.id)

    stored = await service.get_building(city.id, building.id)
    assert stored.level == 1