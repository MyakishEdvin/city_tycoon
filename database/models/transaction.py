"""
Transaction model.

Every balance-changing operation writes exactly one row here alongside
updating User.money, in the same database transaction (see
TransactionService). Rows are never updated or deleted — this table is an
append-only audit log, which is what makes "transaction history" and
future anti-cheat/audit review possible.
"""

from __future__ import annotations

import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        # Powers "transaction history" pagination (most recent first, per user).
        Index("ix_transactions_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="transactions")  # noqa: F821

    # See game.economy.TransactionType for the set of valid values. Stored
    # as text rather than a native SQL enum so new transaction types don't
    # require a migration — only a new enum member in application code.
    type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Signed delta applied to the balance (positive = credit, negative =
    # debit). balance_before/after make every row self-auditing without
    # needing to replay history to reconstruct a point-in-time balance.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_before: Mapped[int] = mapped_column(BigInteger, nullable=False)
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Idempotency key. When provided, a unique constraint prevents the same
    # logical operation (e.g. "daily_reward:2026-09-15:42") from ever being
    # applied twice, even under concurrent duplicate requests. NULL is
    # allowed and multiple NULLs don't collide (standard SQL unique
    # semantics), for transactions that don't need one.
    reference_id: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug convenience only
        return (
            f"<Transaction id={self.id} user_id={self.user_id} type={self.type} "
            f"amount={self.amount} balance_after={self.balance_after}>"
        )
