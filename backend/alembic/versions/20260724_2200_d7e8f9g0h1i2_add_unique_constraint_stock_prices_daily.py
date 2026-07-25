"""add unique constraint to stock_prices_daily

Revision ID: d7e8f9g0h1i2
Revises: c5d6e7f8g9h0
Create Date: 2026-07-24 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7e8f9g0h1i2"
down_revision: Union[str, None] = "c5d6e7f8g9h0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """UNIQUE制約を追加（既存INDEXは削除）"""
    # 既存の通常INDEXを削除（UNIQUE制約で自動作成されるINDEXで代替）
    op.drop_index("idx_stock_prices_daily_code_date", table_name="stock_prices_daily")

    # stock_prices_daily テーブルに UNIQUE 制約を追加
    # ※UNIQUE制約は自動的にUNIQUE INDEXも作成する
    op.create_unique_constraint(
        "uq_stock_prices_daily_code_date",
        "stock_prices_daily",
        ["stock_code", "date"],
    )


def downgrade() -> None:
    """UNIQUE制約を削除（通常INDEXを復元）"""
    # UNIQUE制約を削除
    op.drop_constraint(
        "uq_stock_prices_daily_code_date",
        "stock_prices_daily",
        type_="unique",
    )

    # 元の通常INDEXを復元（存在チェック付き）
    # ※IF NOT EXISTSを使用
    from sqlalchemy import text

    op.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS idx_stock_prices_daily_code_date
            ON stock_prices_daily USING btree (stock_code, date)
            """
        )
    )
