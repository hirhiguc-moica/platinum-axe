"""add_composite_indexes_for_financial_statements

Revision ID: 89cafe627681
Revises: 31b840c92d57
Create Date: 2026-07-31 14:19:17.938019+09:00

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "89cafe627681"
down_revision: str | None = "31b840c92d57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # 複合インデックス1: FY実績データ取得の高速化
    # WHERE stock_code IN (...) AND cur_per_type = 'FY' AND disc_date < ?
    op.create_index(
        "idx_fin_stock_type_date",
        "financial_statements",
        ["stock_code", "cur_per_type", "disc_date"],
        unique=False,
        postgresql_using="btree",
    )

    # 複合インデックス2: 前年同期データ取得の高速化
    # WHERE stock_code = ? AND cur_per_en BETWEEN ? AND ? AND cur_per_type = ?
    op.create_index(
        "idx_fin_stock_peren_type",
        "financial_statements",
        ["stock_code", "cur_per_en", "cur_per_type"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(
        "idx_fin_stock_peren_type",
        table_name="financial_statements",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_fin_stock_type_date",
        table_name="financial_statements",
        postgresql_using="btree",
    )
