from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.city import PlayerCity
from database.models.city_service import CityService
from database.models.transaction import Transaction
from database.models.transaction_service import TransactionService
from database.models.user_service import UserService
from game.economy import (
    DEFAULT_UNLOCKED_DISTRICTS,
    STARTING_BALANCE,
    STARTING_POPULATION,
    InsufficientFundsError,
    TransactionType,
)


async def test_registration_creates_starting_city_and_transaction(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=1001, username="newplayer", first_name="New"
    )

    city = await CityService(session).get_by_user_id(user.id)
    assert city is not None
    assert city.unlocked_districts == DEFAULT_UNLOCKED_DISTRICTS
    assert city.population == STARTING_POPULATION

    history = await TransactionService(session).get_history(user.id)
    assert len(history) == 1
    tx = history[0]
    assert tx.type == TransactionType.STARTING_BALANCE.value
    assert tx.amount == STARTING_BALANCE
    assert tx.balance_before == 0
    assert tx.balance_after == STARTING_BALANCE
    assert tx.reference_id == f"starting_balance:{1001}"


async def test_credit_increases_balance_and_records_transaction(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2001, username="alice", first_name="Alice"
    )
    service = TransactionService(session)

    tx, applied = await service.apply_delta(
        user_id=user.id, delta=500, tx_type=TransactionType.ADMIN_CREDIT
    )

    assert applied is True
    assert tx.balance_before == STARTING_BALANCE
    assert tx.balance_after == STARTING_BALANCE + 500

    await session.refresh(user)
    assert user.money == STARTING_BALANCE + 500


async def test_debit_decreases_balance(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2002, username="bob", first_name="Bob"
    )
    service = TransactionService(session)

    tx, applied = await service.apply_delta(
        user_id=user.id, delta=-300, tx_type=TransactionType.ADMIN_DEBIT
    )

    assert applied is True
    assert tx.amount == -300
    assert tx.balance_after == STARTING_BALANCE - 300

    await session.refresh(user)
    assert user.money == STARTING_BALANCE - 300


async def test_debit_below_zero_is_rejected_and_balance_unchanged(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2003, username="carol", first_name="Carol"
    )
    service = TransactionService(session)

    with pytest.raises(InsufficientFundsError):
        await service.apply_delta(
            user_id=user.id,
            delta=-(STARTING_BALANCE + 1),
            tx_type=TransactionType.ADMIN_DEBIT,
        )

    await session.refresh(user)
    assert user.money == STARTING_BALANCE

    history = await service.get_history(user.id)
    # Only the starting-balance transaction exists — the failed debit
    # never wrote a row.
    assert len(history) == 1


async def test_duplicate_reference_id_is_idempotent(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2004, username="dave", first_name="Dave"
    )
    service = TransactionService(session)
    ref = "daily_reward:2026-09-15:2004"

    tx1, applied1 = await service.apply_delta(
        user_id=user.id, delta=1000, tx_type=TransactionType.ADMIN_CREDIT, reference_id=ref
    )
    tx2, applied2 = await service.apply_delta(
        user_id=user.id, delta=1000, tx_type=TransactionType.ADMIN_CREDIT, reference_id=ref
    )

    assert applied1 is True
    assert applied2 is False
    assert tx1.id == tx2.id

    await session.refresh(user)
    # Balance only changed once, not twice.
    assert user.money == STARTING_BALANCE + 1000


async def test_reference_id_uniqueness_is_enforced_at_db_level(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2005, username="erin", first_name="Erin"
    )

    duplicate = Transaction(
        user_id=user.id,
        type=TransactionType.ADMIN_CREDIT.value,
        amount=10,
        balance_before=STARTING_BALANCE,
        balance_after=STARTING_BALANCE + 10,
        reference_id=f"starting_balance:{2005}",  # already used by registration
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


async def test_get_history_orders_most_recent_first(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2006, username="frank", first_name="Frank"
    )
    service = TransactionService(session)

    await service.apply_delta(user_id=user.id, delta=100, tx_type=TransactionType.ADMIN_CREDIT)
    await service.apply_delta(user_id=user.id, delta=200, tx_type=TransactionType.ADMIN_CREDIT)

    history = await service.get_history(user.id, limit=2)
    assert [tx.amount for tx in history] == [200, 100]


async def test_city_display_names_maps_known_districts(session):
    user, _ = await UserService(session).get_or_create(
        telegram_id=2007, username="grace", first_name="Grace"
    )
    city = await CityService(session).get_by_user_id(user.id)

    assert CityService.display_names(city) == ["Old Town"]
