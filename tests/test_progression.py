from __future__ import annotations

import pytest

from database.models.progression_service import ProgressionService
from database.models.user_service import UserService
from game.progression import level_progress_fraction, xp_required_for_level


def test_xp_required_for_level_grows_linearly():
    assert xp_required_for_level(1) == 100
    assert xp_required_for_level(2) == 150
    assert xp_required_for_level(3) == 200


def test_xp_required_for_level_rejects_invalid_level():
    with pytest.raises(ValueError):
        xp_required_for_level(0)


def test_level_progress_fraction_bounds():
    assert level_progress_fraction(1, 0) == 0.0
    assert level_progress_fraction(1, 50) == 0.5
    assert level_progress_fraction(1, 100) == 1.0
    # Never exceeds 1.0 even if xp somehow overshoots.
    assert level_progress_fraction(1, 500) == 1.0


async def test_add_xp_below_threshold_does_not_level_up(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=3001, username="alice", first_name="Alice"
    )
    service = ProgressionService(session)

    result = await service.add_xp(user, 40)

    assert result.levels_gained == 0
    assert result.user.level == 1
    assert result.user.xp == 40


async def test_add_xp_triggers_single_level_up_with_remainder(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=3002, username="bob", first_name="Bob"
    )
    service = ProgressionService(session)

    # Level 1 requires 100 XP; 120 should level up once with 20 remaining.
    result = await service.add_xp(user, 120)

    assert result.levels_gained == 1
    assert result.user.level == 2
    assert result.user.xp == 20


async def test_add_xp_can_trigger_multiple_level_ups_at_once(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=3003, username="carol", first_name="Carol"
    )
    service = ProgressionService(session)

    # Level 1 needs 100, level 2 needs 150 -> 260 XP crosses both.
    result = await service.add_xp(user, 260)

    assert result.levels_gained == 2
    assert result.user.level == 3
    assert result.user.xp == 10


async def test_add_xp_zero_is_a_no_op(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=3004, username="dave", first_name="Dave"
    )
    service = ProgressionService(session)

    result = await service.add_xp(user, 0)

    assert result.levels_gained == 0
    assert result.user.xp == 0


async def test_add_xp_rejects_negative_amount(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=3005, username="erin", first_name="Erin"
    )
    service = ProgressionService(session)

    with pytest.raises(ValueError):
        await service.add_xp(user, -10)