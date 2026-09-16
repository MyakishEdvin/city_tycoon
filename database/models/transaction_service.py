"""
TransactionService: the only code path allowed to change User.money.

Every balance change — regardless of which future subsystem triggers it
(businesses, quests, marketplace, admin tools) — must go through
`apply_delta`. It is the single place that enforces:

  * server-authoritative balances (callers pass a signed delta computed
    from trusted server-side data, never a client-supplied balance)
  * no negative balances
  * atomicity (balance update + audit row in one DB transaction)
  * row locking (SELECT ... FOR UPDATE) to make concurrent operations on
    the same user safe
  * idempotency via an optional reference_id, so a retried or duplicated
    request can never be applied twice
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.transaction import Transaction
from database.models.user import User
from game.economy import InsufficientFundsError, TransactionType

logger = logging.getLogger("city_tycoon.transaction_service")


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_reference_id(self, reference_id: str) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.reference_id == reference_id)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[Transaction]:
        """Most-recent-first, paginated — never loads a user's full history."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            # Order by id, not created_at: two transactions can land in
            # the same second under DB timestamp resolution (notably
            # SQLite's CURRENT_TIMESTAMP), which would make created_at
            # ordering ambiguous/flaky. id is monotonic on insert.
            .order_by(Transaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def apply_delta(
        self,
        *,
        user_id: int,
        delta: int,
        tx_type: TransactionType,
        reference_id: str | None = None,
    ) -> tuple[Transaction, bool]:
        """
        Apply a signed balance change to a user, atomically.

        Returns (transaction, applied):
          * applied=True  -> this call actually changed the balance.
          * applied=False -> a transaction with this reference_id already
            existed, so nothing was re-applied; the existing row is
            returned as-is (idempotent no-op).

        Raises InsufficientFundsError if the delta would take the balance
        below zero. Never lets the balance go negative, and never applies
        the same reference_id twice, even under concurrent duplicate calls.
        """
        if delta == 0:
            raise ValueError("delta must be non-zero")

        if reference_id:
            existing = await self.get_by_reference_id(reference_id)
            if existing is not None:
                logger.info(
                    "Duplicate transaction ignored: reference_id=%s user_id=%s",
                    reference_id,
                    user_id,
                )
                return existing, False

        # Lock the user row for the duration of this transaction so two
        # concurrent operations on the same user (e.g. two purchases fired
        # at once) serialize instead of racing on a stale balance read.
        result = await self.session.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} does not exist")

        balance_before = user.money
        balance_after = balance_before + delta

        if balance_after < 0:
            await self.session.rollback()
            raise InsufficientFundsError(
                user_id=user_id, balance=balance_before, requested=-delta
            )

        user.money = balance_after

        transaction = Transaction(
            user_id=user_id,
            type=tx_type.value,
            amount=delta,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_id=reference_id,
        )
        self.session.add(transaction)

        try:
            await self.session.commit()
        except IntegrityError:
            # Race: another concurrent request committed a transaction
            # with the same reference_id between our existence check and
            # our commit. Roll back this attempt entirely (balance change
            # included) and return the winner's row instead.
            await self.session.rollback()
            if reference_id:
                existing = await self.get_by_reference_id(reference_id)
                if existing is not None:
                    logger.warning(
                        "Race on reference_id=%s user_id=%s — returning existing transaction",
                        reference_id,
                        user_id,
                    )
                    return existing, False
            raise

        await self.session.refresh(transaction)
        logger.info(
            "Transaction applied: user_id=%s type=%s delta=%s balance_after=%s reference_id=%s",
            user_id,
            tx_type.value,
            delta,
            balance_after,
            reference_id,
        )
        return transaction, True
