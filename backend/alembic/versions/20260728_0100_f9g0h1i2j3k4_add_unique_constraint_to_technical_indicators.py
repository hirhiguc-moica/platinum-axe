"""add unique constraint to technical indicators

Revision ID: f9g0h1i2j3k4
Revises: e8f9g0h1i2j3
Create Date: 2026-07-28 01:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f9g0h1i2j3k4"
down_revision: str | None = "e8f9g0h1i2j3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """technical_indicators テーブルに UNIQUE制約を追加"""
    op.create_unique_constraint(
        "uq_technical_indicators_code_date",
        "technical_indicators",
        ["stock_code", "date"],
    )


def downgrade() -> None:
    """UNIQUE制約を削除"""
    op.drop_constraint(
        "uq_technical_indicators_code_date",
        "technical_indicators",
        type_="unique",
    )
