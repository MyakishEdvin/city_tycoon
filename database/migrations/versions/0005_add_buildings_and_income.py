"""add player_buildings table and last_income_at column

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-17 00:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "player_cities",
        sa.Column(
            "last_income_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "player_buildings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("building_type", sa.String(length=32), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["city_id"], ["player_cities.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_player_buildings_city_id", "player_buildings", ["city_id"])


def downgrade() -> None:
    op.drop_index("ix_player_buildings_city_id", table_name="player_buildings")
    op.drop_table("player_buildings")
    op.drop_column("player_cities", "last_income_at")