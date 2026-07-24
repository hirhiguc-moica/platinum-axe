"""replace markets with JPX official codes

Revision ID: b3c4d5e6f7g8
Revises: a1b2c3d4e5f6
Create Date: 2026-07-24 02:00:00.000000

市場マスタ（markets）をJPX公式コードで置き換え
- 旧データ（PRIME, STANDARD等）を削除
- JPX公式コード（0111, 0112等）で再作成
- 外部キー制約のため、stock_masterのデータも削除
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "b3c4d5e6f7g8"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. stock_masterのデータ削除（外部キー制約のため先に削除）
    op.execute("DELETE FROM stock_master")

    # 2. marketsのデータ削除
    op.execute("DELETE FROM markets")

    # 3. JPX公式の市場マスタデータINSERT
    op.execute(
        """
        INSERT INTO markets (
            market_code,
            market_name,
            market_short_name,
            market_abbreviation,
            market_category,
            market_type,
            sort_order
        ) VALUES
        -- 新市場区分（2022年4月以降）
        ('0111', 'プライム', 'プライム', 'PR', 'PRIME', '内国株式', 1),
        ('0112', 'スタンダード', 'スタンダード', 'ST', 'STANDARD', '内国株式', 2),
        ('0113', 'グロース', 'グロース', 'GR', 'GROWTH', '内国株式', 3),

        -- 旧市場区分（2022年4月以前）
        ('0101', '東証一部', '東証一部', '東1', 'LEGACY', '内国株式', 11),
        ('0102', '東証二部', '東証二部', '東2', 'LEGACY', '内国株式', 12),
        ('0104', 'マザーズ', 'マザーズ', 'MTH', 'LEGACY', '内国株式', 14),
        ('0106', 'JASDAQ スタンダード', 'JASDAQ STD', 'JQ-STD', 'LEGACY', '内国株式', 16),
        ('0107', 'JASDAQ グロース', 'JASDAQ GRW', 'JQ-GRW', 'LEGACY', '内国株式', 17),

        -- その他
        ('0105', 'TOKYO PRO MARKET', 'PRO Market', 'PRO', 'OTHER', '内国株式', 15),
        ('0109', 'その他', 'その他', 'OTHER', 'OTHER', '内国株式', 99)
        """
    )


def downgrade() -> None:
    # 1. stock_masterのデータ削除
    op.execute("DELETE FROM stock_master")

    # 2. marketsのデータ削除
    op.execute("DELETE FROM markets")

    # 3. 旧データに戻す
    op.execute(
        """
        INSERT INTO markets (
            market_code,
            market_name,
            market_short_name,
            market_abbreviation,
            market_category,
            market_type,
            sort_order
        ) VALUES
        ('PRIME', 'プライム（内国株式）', 'プライム', 'PR', 'PRIME', '内国株式', 1),
        ('STANDARD', 'スタンダード（内国株式）', 'スタンダード', 'ST', 'STANDARD', '内国株式', 2),
        ('GROWTH', 'グロース（内国株式）', 'グロース', 'GR', 'GROWTH', '内国株式', 3),
        ('PRIME_F', 'プライム（外国株式）', 'プライム外国', 'PR(外)', 'PRIME', '外国株式', 4),
        ('STANDARD_F', 'スタンダード（外国株式）', 'スタンダード外国', 'ST(外)', 'STANDARD', '外国株式', 5),
        ('GROWTH_F', 'グロース（外国株式）', 'グロース外国', 'GR(外)', 'GROWTH', '外国株式', 6)
        """
    )
