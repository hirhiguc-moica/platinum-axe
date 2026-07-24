"""change volume columns to bigint

Revision ID: e8f9g0h1i2j3
Revises: d7e8f9g0h1i2
Create Date: 2026-07-24 23:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e8f9g0h1i2j3"
down_revision: Union[str, None] = "d7e8f9g0h1i2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """volume と adjusted_volume を INTEGER から BIGINT に変更"""
    # volume を BIGINT に変更
    op.alter_column(
        "stock_prices_daily",
        "volume",
        existing_type=sa.INTEGER(),
        type_=sa.BIGINT(),
        existing_nullable=True,
        existing_comment="出来高",
    )

    # adjusted_volume を BIGINT に変更
    op.alter_column(
        "stock_prices_daily",
        "adjusted_volume",
        existing_type=sa.INTEGER(),
        type_=sa.BIGINT(),
        existing_nullable=True,
        existing_comment="調整後出来高",
    )


def downgrade() -> None:
    """BIGINT から INTEGER に戻す"""
    # adjusted_volume を INTEGER に戻す
    op.alter_column(
        "stock_prices_daily",
        "adjusted_volume",
        existing_type=sa.BIGINT(),
        type_=sa.INTEGER(),
        existing_nullable=True,
        existing_comment="調整後出来高",
    )

    # volume を INTEGER に戻す
    op.alter_column(
        "stock_prices_daily",
        "volume",
        existing_type=sa.BIGINT(),
        type_=sa.INTEGER(),
        existing_nullable=True,
        existing_comment="出来高",
    )
