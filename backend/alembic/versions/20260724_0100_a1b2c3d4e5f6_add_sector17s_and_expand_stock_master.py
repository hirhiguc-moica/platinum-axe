"""add sector17s and expand stock_master

Revision ID: a1b2c3d4e5f6
Revises: db42c44b1ad6
Create Date: 2026-07-24 01:00:00.000000+09:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "db42c44b1ad6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # 1. sector17sテーブル作成
    op.create_table(
        "sector17s",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="主キー",
        ),
        sa.Column(
            "sector17_code",
            sa.String(length=10),
            nullable=False,
            comment="17業種コード（J-Quants API）",
        ),
        sa.Column("sector17_name", sa.String(length=100), nullable=False, comment="17業種名"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="更新日時",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sector17s")),
        sa.UniqueConstraint("sector17_code", name=op.f("uq_sector17s_sector17_code")),
        comment="17業種マスタ（JPX分類）",
    )
    op.create_index(
        op.f("ix_sector17s_sector17_code"), "sector17s", ["sector17_code"], unique=True
    )

    # 2. sector17sマスタデータINSERT
    op.execute(
        """
        INSERT INTO sector17s (sector17_code, sector17_name) VALUES
        ('1', '食品'),
        ('2', 'エネルギー資源'),
        ('3', '建設・資材'),
        ('4', '素材・化学'),
        ('5', '医薬品'),
        ('6', '自動車・輸送機'),
        ('7', '鉄鋼・非鉄'),
        ('8', '機械'),
        ('9', '電機・精密'),
        ('10', '情報通信・サービスその他'),
        ('11', '電気・ガス'),
        ('12', '運輸・物流'),
        ('13', '商社・卸売'),
        ('14', '小売'),
        ('15', '銀行'),
        ('16', '金融（除く銀行）'),
        ('17', '不動産'),
        ('99', 'その他')
        """
    )

    # 3. stock_masterテーブルへのカラム追加
    op.add_column(
        "stock_master",
        sa.Column(
            "info_date",
            sa.DATE(),
            nullable=True,  # 一旦NULLable、後でNOT NULLに変更
            comment="情報適用年月日（APIのDateフィールド、更新判断に使用）",
        ),
    )
    op.add_column(
        "stock_master",
        sa.Column(
            "sector17_code",
            sa.String(length=10),
            nullable=True,
            comment="17業種コード",
        ),
    )
    op.add_column(
        "stock_master",
        sa.Column(
            "scale_category",
            sa.String(length=50),
            nullable=True,
            comment="規模区分（TOPIX分類: TOPIX Core30, Large70, Mid400, Small 1/2）",
        ),
    )
    op.add_column(
        "stock_master",
        sa.Column(
            "margin_code",
            sa.String(length=10),
            nullable=True,
            comment="信用区分コード（1: 信用 / 2: 貸借 / 3: その他）",
        ),
    )

    # 4. 外部キー制約追加
    op.create_foreign_key(
        op.f("fk_stock_master_sector17_code_sector17s"),
        "stock_master",
        "sector17s",
        ["sector17_code"],
        ["sector17_code"],
    )

    # 5. インデックス追加
    op.create_index(
        op.f("ix_stock_master_sector17_code"), "stock_master", ["sector17_code"], unique=False
    )
    op.create_index(
        op.f("ix_stock_master_info_date"), "stock_master", ["info_date"], unique=False
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # インデックス削除
    op.drop_index(op.f("ix_stock_master_info_date"), table_name="stock_master")
    op.drop_index(op.f("ix_stock_master_sector17_code"), table_name="stock_master")

    # 外部キー制約削除
    op.drop_constraint(
        op.f("fk_stock_master_sector17_code_sector17s"), "stock_master", type_="foreignkey"
    )

    # stock_masterカラム削除
    op.drop_column("stock_master", "margin_code")
    op.drop_column("stock_master", "scale_category")
    op.drop_column("stock_master", "sector17_code")
    op.drop_column("stock_master", "info_date")

    # sector17sテーブル削除
    op.drop_index(op.f("ix_sector17s_sector17_code"), table_name="sector17s")
    op.drop_table("sector17s")
