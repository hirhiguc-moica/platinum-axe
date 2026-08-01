"""Add fundamental_indicators table

Revision ID: 31b840c92d57
Revises: 9cbb0776b974
Create Date: 2026-07-31 12:00:00.000000+09:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "31b840c92d57"
down_revision: str | None = "9cbb0776b974"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "fundamental_indicators",
        # Primary key and timestamps (from TimestampMixin)
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="ID",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新日時",
        ),
        # Stock identification
        sa.Column("stock_code", sa.String(length=10), nullable=False, comment="銘柄コード"),
        sa.Column("date", sa.Date(), nullable=False, comment="日付"),
        # 1. Valuation indicators (6 items)
        sa.Column(
            "per",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="PER（株価収益率、実績）",
        ),
        sa.Column(
            "pbr",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="PBR（株価純資産倍率）",
        ),
        sa.Column(
            "psr",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="PSR（株価売上高倍率）",
        ),
        sa.Column(
            "pcfr",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="PCFR（株価キャッシュフロー倍率）",
        ),
        sa.Column(
            "forward_per_fy",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="予想PER（当期）",
        ),
        sa.Column(
            "forward_per_nx",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="予想PER（翌期）",
        ),
        # 2. Profitability indicators (4 items)
        sa.Column(
            "roe",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="ROE（自己資本利益率）",
        ),
        sa.Column(
            "roa",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="ROA（総資産利益率）",
        ),
        sa.Column(
            "operating_margin",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="営業利益率",
        ),
        sa.Column(
            "net_margin",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="純利益率",
        ),
        # 3. Growth indicators (5 items, YoY)
        sa.Column(
            "sales_growth_yoy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="売上高成長率（前年同期比）",
        ),
        sa.Column(
            "op_growth_yoy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="営業利益成長率（前年同期比）",
        ),
        sa.Column(
            "np_growth_yoy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="純利益成長率（前年同期比）",
        ),
        sa.Column(
            "eps_growth_yoy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="EPS成長率（前年同期比）",
        ),
        sa.Column(
            "cfo_growth_yoy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="営業CF成長率（前年同期比）",
        ),
        # 4. Safety indicators (1 item)
        sa.Column(
            "equity_ratio",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="自己資本比率",
        ),
        # 5. Dividend indicators (4 items)
        sa.Column(
            "dividend_yield",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="配当利回り（実績）",
        ),
        sa.Column(
            "payout_ratio",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="配当性向（実績）",
        ),
        sa.Column(
            "forward_div_yield_fy",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="予想配当利回り（当期）",
        ),
        sa.Column(
            "forward_div_yield_nx",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="予想配当利回り（翌期）",
        ),
        # Meta information
        sa.Column("calculated_at", sa.Date(), nullable=False, comment="計算日時"),
        # Constraints
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fundamental_indicators")),
        sa.UniqueConstraint(
            "stock_code",
            "date",
            name="uq_fundamental_indicators_code_date",
        ),
        comment="ファンダメンタル指標（20項目）",
    )
    # Create indexes
    op.create_index(
        "idx_fundamental_indicators_code_date",
        "fundamental_indicators",
        ["stock_code", "date"],
        unique=False,
        postgresql_using="btree",
    )
    op.create_index(
        "idx_fundamental_indicators_date",
        "fundamental_indicators",
        ["date"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(
        "idx_fundamental_indicators_date",
        table_name="fundamental_indicators",
        postgresql_using="btree",
    )
    op.drop_index(
        "idx_fundamental_indicators_code_date",
        table_name="fundamental_indicators",
        postgresql_using="btree",
    )
    op.drop_table("fundamental_indicators")
