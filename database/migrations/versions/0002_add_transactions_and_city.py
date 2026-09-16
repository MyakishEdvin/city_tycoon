"""add transactions and player_cities tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("balance_before", sa.BigInteger(), nullable=False),
        sa.Column("balance_after", sa.BigInteger(), nullable=False),
        sa.Column("reference_id", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_transactions_user_id_created_at", "transactions", ["user_id", "created_at"]
    )
    op.create_index(
        "ix_transactions_reference_id", "transactions", ["reference_id"], unique=True
    )

    op.create_table(
        "player_cities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("unlocked_districts", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_player_cities_user_id", "player_cities", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_player_cities_user_id", table_name="player_cities")
    op.drop_table("player_cities")

    op.drop_index("ix_transactions_reference_id", table_name="transactions")
    op.drop_index("ix_transactions_user_id_created_at", table_name="transactions")
    op.drop_table("transactions")


