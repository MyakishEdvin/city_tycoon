"""add population column to player_cities

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16 12:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "player_cities",
        sa.Column("population", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("player_cities", "population")