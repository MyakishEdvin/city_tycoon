from __future__ import annotations

from database.models.user import STARTING_BALANCE
from database.models.user_service import UserService


async def test_new_user_gets_starting_balance_and_defaults(session):
    service = UserService(session)

    user, created = await service.get_or_create(
        telegram_id=111, username="alice", first_name="Alice"
    )

    assert created is True
    assert user.telegram_id == 111
    assert user.money == STARTING_BALANCE
    assert user.level == 1
    assert user.xp == 0
    assert user.referral_code is not None


async def test_start_is_idempotent_and_never_resets_progress(session):
    service = UserService(session)

    user, created = await service.get_or_create(
        telegram_id=222, username="bob", first_name="Bob"
    )
    assert created is True

    # Simulate progress that would happen via gameplay in later phases.
    user.money = 50_000
    user.level = 5
    await session.commit()

    same_user, created_again = await service.get_or_create(
        telegram_id=222, username="bob_new_handle", first_name="Bob"
    )

    assert created_again is False
    assert same_user.id == user.id
    # Progress must survive a repeated /start.
    assert same_user.money == 50_000
    assert same_user.level == 5
    # Denormalized profile fields still refresh.
    assert same_user.username == "bob_new_handle"


async def test_referral_code_links_referrer(session):
    service = UserService(session)

    referrer, _ = await service.get_or_create(
        telegram_id=333, username="referrer", first_name="Ref"
    )

    referred, created = await service.get_or_create(
        telegram_id=444,
        username="newbie",
        first_name="New",
        referral_code=referrer.referral_code,
    )

    assert created is True
    assert referred.referred_by_id == referrer.id


async def test_self_referral_is_ignored(session):
    service = UserService(session)

    user, created = await service.get_or_create(
        telegram_id=555,
        username="lonewolf",
        first_name="Lone",
        referral_code="does-not-exist-yet",
    )

    assert created is True
    assert user.referred_by_id is None


async def test_unknown_referral_code_does_not_fail_registration(session):
    service = UserService(session)

    user, created = await service.get_or_create(
        telegram_id=666,
        username="someone",
        first_name="Someone",
        referral_code="totally-invalid-code",
    )

    assert created is True
    assert user.referred_by_id is None
