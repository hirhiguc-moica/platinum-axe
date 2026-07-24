"""replace sectors with official 33+1 sector codes

Revision ID: c5d6e7f8g9h0
Revises: b3c4d5e6f7g8
Create Date: 2026-07-24 02:10:00.000000

業種マスタ（sectors）を東証公式33業種+9999で置き換え
- 旧データ（seedスクリプトのモックデータ）を削除
- 東証公式33業種 + 9999（その他、業種なし）で再作成
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c5d6e7f8g9h0"
down_revision = "b3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 既存データ削除
    op.execute("DELETE FROM sectors")

    # 2. 東証公式33業種 + 9999（業種なし）をINSERT
    op.execute(
        """
        INSERT INTO sectors (sector_code, sector_name, sector_name_en) VALUES
        ('0050', '水産・農林業', 'Fishery, Agriculture & Forestry'),
        ('1050', '鉱業', 'Mining'),
        ('2050', '建設業', 'Construction'),
        ('3050', '食料品', 'Foods'),
        ('3100', '繊維製品', 'Textiles & Apparels'),
        ('3150', 'パルプ・紙', 'Pulp & Paper'),
        ('3200', '化学', 'Chemicals'),
        ('3250', '医薬品', 'Pharmaceutical'),
        ('3300', '石油・石炭製品', 'Oil & Coal Products'),
        ('3350', 'ゴム製品', 'Rubber Products'),
        ('3400', 'ガラス・土石製品', 'Glass & Ceramics Products'),
        ('3450', '鉄鋼', 'Iron & Steel'),
        ('3500', '非鉄金属', 'Nonferrous Metals'),
        ('3550', '金属製品', 'Metal Products'),
        ('3600', '機械', 'Machinery'),
        ('3650', '電気機器', 'Electric Appliances'),
        ('3700', '輸送用機器', 'Transportation Equipment'),
        ('3750', '精密機器', 'Precision Instruments'),
        ('3800', 'その他製品', 'Other Products'),
        ('4050', '電気・ガス業', 'Electric Power & Gas'),
        ('5050', '陸運業', 'Land Transportation'),
        ('5100', '海運業', 'Marine Transportation'),
        ('5150', '空運業', 'Air Transportation'),
        ('5200', '倉庫・運輸関連業', 'Warehousing & Harbor Transportation Services'),
        ('5250', '情報・通信業', 'Information & Communication'),
        ('6050', '卸売業', 'Wholesale Trade'),
        ('6100', '小売業', 'Retail Trade'),
        ('7050', '銀行業', 'Banks'),
        ('7100', '証券、商品先物取引業', 'Securities & Commodity Futures'),
        ('7150', '保険業', 'Insurance'),
        ('7200', 'その他金融業', 'Other Financing Business'),
        ('8050', '不動産業', 'Real Estate'),
        ('9050', 'サービス業', 'Services'),
        ('9999', 'その他（業種なし）', 'Other (No Sector)')
        """
    )


def downgrade() -> None:
    # rollback用（旧データに戻す）
    op.execute("DELETE FROM sectors")
    # Note: 旧データは復元しない（seedスクリプトで再投入すること）
