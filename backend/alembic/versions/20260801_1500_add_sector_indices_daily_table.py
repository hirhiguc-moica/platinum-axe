"""add sector_indices_daily table

Revision ID: a1b2c3d4e5f6
Revises: 89cafe627681
Create Date: 2026-08-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c90dba26d83f'
down_revision: Union[str, None] = '89cafe627681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """セクター指数日次データテーブルを作成"""
    op.create_table(
        'sector_indices_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('index_code', sa.String(4), nullable=False, comment='指数コード（例: 0000, 0080）'),
        sa.Column('index_name', sa.String(50), nullable=False, comment='指数名（例: TOPIX, 食品）'),
        sa.Column('date', sa.Date(), nullable=False, comment='日付'),

        # 生データ（J-Quants APIから取得、機械学習用、FE表示不可）
        sa.Column('open', sa.Numeric(10, 2), nullable=False, comment='始値'),
        sa.Column('high', sa.Numeric(10, 2), nullable=False, comment='高値'),
        sa.Column('low', sa.Numeric(10, 2), nullable=False, comment='安値'),
        sa.Column('close', sa.Numeric(10, 2), nullable=False, comment='終値'),

        # 計算済み騰落率（FE表示可）
        sa.Column('change_rate_1d', sa.Numeric(10, 4), nullable=True, comment='前日比騰落率（%）'),
        sa.Column('change_rate_5d', sa.Numeric(10, 4), nullable=True, comment='5日前比騰落率（%）'),
        sa.Column('change_rate_20d', sa.Numeric(10, 4), nullable=True, comment='20日前比騰落率（%）'),
        sa.Column('change_rate_60d', sa.Numeric(10, 4), nullable=True, comment='60日前比騰落率（%）'),

        # タイムスタンプ
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        # UNIQUE制約
        sa.UniqueConstraint('index_code', 'date', name='uq_sector_indices_daily_code_date'),

        comment='セクター指数日次データ（全47指数、Phase 1では34指数を機械学習に使用）'
    )

    # インデックス作成
    op.create_index('ix_sector_indices_daily_index_code', 'sector_indices_daily', ['index_code'])
    op.create_index('ix_sector_indices_daily_date', 'sector_indices_daily', ['date'])
    op.create_index('ix_sector_indices_daily_code_date', 'sector_indices_daily', ['index_code', 'date'])


def downgrade() -> None:
    """セクター指数日次データテーブルを削除"""
    op.drop_index('ix_sector_indices_daily_code_date', table_name='sector_indices_daily')
    op.drop_index('ix_sector_indices_daily_date', table_name='sector_indices_daily')
    op.drop_index('ix_sector_indices_daily_index_code', table_name='sector_indices_daily')
    op.drop_table('sector_indices_daily')
