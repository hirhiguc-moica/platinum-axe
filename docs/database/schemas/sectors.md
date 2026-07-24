# sectors（業種マスタ）

## 概要

東京証券取引所の業種マスタデータ（33業種分類）

## データソース

- **データ取得方法**: 手動管理
- **更新頻度**: 不定期
- **Layer**: Layer 1 (Raw Data - マスタデータ)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `sector_code` | VARCHAR(10) | NOT NULL | 業種コード（33業種分類） |
| `sector_name` | VARCHAR(100) | NOT NULL | 業種名 |
| `sector_name_en` | VARCHAR(100) | NULL | 業種名（英語） |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `ix_sectors_sector_code` (sector_code) - UNIQUE

## 登録データ（33件）

水産・農林業、鉱業、建設業、食料品、繊維製品、パルプ・紙、化学、医薬品、石油・石炭製品、ゴム製品、ガラス・土石製品、鉄鋼、非鉄金属、金属製品、機械、電気機器、輸送用機器、精密機器、その他製品、電気・ガス業、陸運業、海運業、空運業、倉庫・運輸関連業、情報・通信業、卸売業、小売業、銀行業、証券・商品先物取引業、保険業、その他金融業、不動産業、サービス業

## 関連テーブル

- [`stock_master`](./stock_master.md) - 銘柄マスタ（`sector_code`で紐付け）

## ソースコード

- **Alembic**: [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L128-L159)
