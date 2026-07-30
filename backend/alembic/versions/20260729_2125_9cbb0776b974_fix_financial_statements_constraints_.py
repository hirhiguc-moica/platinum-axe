"""fix_financial_statements_constraints_and_bigint

Revision ID: 9cbb0776b974
Revises: fa58d7eb71d8
Create Date: 2026-07-29 21:25:35.839242+09:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9cbb0776b974"
down_revision: str | None = "fa58d7eb71d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # 1. 既存のUNIQUE制約を削除
    op.drop_constraint(
        "uq_financial_statements_code_date_type",
        "financial_statements",
        type_="unique",
    )

    # 2. 株式数カラムをBIGINTに変更（INTEGER範囲オーバー対策）
    op.alter_column(
        "financial_statements",
        "sh_out_fy",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        existing_comment="期末発行済株式数（千株）",
    )
    op.alter_column(
        "financial_statements",
        "tr_sh_fy",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        existing_comment="期末自己株式数（千株）",
    )
    op.alter_column(
        "financial_statements",
        "avg_sh",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        existing_comment="期中平均株式数（千株）",
    )

    # 3. disc_timeをNOT NULLに変更（データ整合性担保）
    op.alter_column(
        "financial_statements",
        "disc_time",
        existing_type=sa.String(length=20),
        nullable=False,
        existing_comment="開示時刻",
    )

    # 4. 新しいUNIQUE制約を追加（ナチュラルキー: 冪等性担保）
    op.create_unique_constraint(
        "uq_financial_statements_natural_key",
        "financial_statements",
        ["stock_code", "disc_date", "type_of_document", "disc_time"],
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # 1. 新しいUNIQUE制約を削除
    op.drop_constraint(
        "uq_financial_statements_natural_key",
        "financial_statements",
        type_="unique",
    )

    # 2. disc_timeをNULL許容に戻す
    op.alter_column(
        "financial_statements",
        "disc_time",
        existing_type=sa.String(length=20),
        nullable=True,
        existing_comment="開示時刻",
    )

    # 3. 株式数カラムをINTEGERに戻す
    op.alter_column(
        "financial_statements",
        "sh_out_fy",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        existing_comment="期末発行済株式数（千株）",
    )
    op.alter_column(
        "financial_statements",
        "tr_sh_fy",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        existing_comment="期末自己株式数（千株）",
    )
    op.alter_column(
        "financial_statements",
        "avg_sh",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        existing_comment="期中平均株式数（千株）",
    )

    # 4. 元のUNIQUE制約を復元
    op.create_unique_constraint(
        "uq_financial_statements_code_date_type",
        "financial_statements",
        ["stock_code", "disc_date", "type_of_document"],
    )
