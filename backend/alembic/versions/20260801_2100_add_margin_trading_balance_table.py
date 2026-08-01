"""add margin_trading_balance table

Revision ID: d1e2f3g4h5i6
Revises: c90dba26d83f
Create Date: 2026-08-01 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3g4h5i6'
down_revision: Union[str, None] = 'c90dba26d83f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """信用取引週末残高データテーブルを作成"""
    op.create_table(
        'margin_trading_balance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('stock_code', sa.String(10), sa.ForeignKey('stock_master.stock_code'), nullable=False, comment='銘柄コード'),
        sa.Column('date', sa.Date(), nullable=False, comment='週末日付（通常金曜日）'),

        # 生データ（J-Quants APIレスポンス、DB内部のみ保存、Web表示禁止）
        sa.Column('short_vol', sa.BigInteger(), nullable=False, comment='売合計信用残高（株数）'),
        sa.Column('long_vol', sa.BigInteger(), nullable=False, comment='買合計信用残高（株数）'),
        sa.Column('short_neg_vol', sa.BigInteger(), nullable=False, comment='一般信用取引売残高（株数）'),
        sa.Column('long_neg_vol', sa.BigInteger(), nullable=False, comment='一般信用取引買残高（株数）'),
        sa.Column('short_std_vol', sa.BigInteger(), nullable=False, comment='制度信用取引売残高（株数）'),
        sa.Column('long_std_vol', sa.BigInteger(), nullable=False, comment='制度信用取引買残高（株数）'),
        sa.Column('iss_type', sa.String(1), nullable=False, comment='銘柄区分（1:信用、2:貸借、3:その他）'),

        # 計算済み指標（Web/API表示可、機械学習特徴量）
        sa.Column('margin_ratio', sa.Numeric(10, 4), nullable=True, comment='信用倍率（買い残 ÷ 売り残）'),
        sa.Column('long_vol_change', sa.BigInteger(), nullable=True, comment='買い残前週比増減（株数）'),
        sa.Column('short_vol_change', sa.BigInteger(), nullable=True, comment='売り残前週比増減（株数）'),
        sa.Column('long_vol_change_rate', sa.Numeric(10, 4), nullable=True, comment='買い残前週比増減率（%）'),
        sa.Column('short_vol_change_rate', sa.Numeric(10, 4), nullable=True, comment='売り残前週比増減率（%）'),

        # タイムスタンプ
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        # UNIQUE制約
        sa.UniqueConstraint('stock_code', 'date', name='uq_margin_trading_balance_code_date'),

        comment='信用取引週末残高データ（週次、全銘柄）'
    )

    # インデックス作成
    op.create_index('ix_margin_trading_balance_stock_code', 'margin_trading_balance', ['stock_code'])
    op.create_index('ix_margin_trading_balance_date', 'margin_trading_balance', ['date'])
    op.create_index('ix_margin_trading_balance_code_date', 'margin_trading_balance', ['stock_code', 'date'])


def downgrade() -> None:
    """信用取引週末残高データテーブルを削除"""
    op.drop_index('ix_margin_trading_balance_code_date', table_name='margin_trading_balance')
    op.drop_index('ix_margin_trading_balance_date', table_name='margin_trading_balance')
    op.drop_index('ix_margin_trading_balance_stock_code', table_name='margin_trading_balance')
    op.drop_table('margin_trading_balance')
