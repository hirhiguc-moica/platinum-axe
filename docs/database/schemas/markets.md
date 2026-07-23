# markets（市場区分マスタ）

## 概要

東京証券取引所の市場区分マスタデータ（Prime, Standard, Growth等）

## データソース

- **データ取得方法**: 手動管理
- **更新頻度**: 不定期
- **更新時刻**: -
- **更新ジョブ**: -

## Layer

- **Layer 1**: Raw Data（マスタデータ）

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー（UUID、自動生成） |
| `market_code` | VARCHAR(10) | NOT NULL | 市場コード（J-Quants API） |
| `market_name` | VARCHAR(100) | NOT NULL | 市場名 |
| `market_short_name` | VARCHAR(50) | NOT NULL | 短縮名 |
| `market_abbreviation` | VARCHAR(10) | NOT NULL | 略号（PR/ST/GR等） |
| `market_category` | VARCHAR(50) | NOT NULL | カテゴリ（PRIME/STANDARD/GROWTH） |
| `market_type` | VARCHAR(50) | NULL | 市場種別（内国株式/外国株式） |
| `sort_order` | INTEGER | NOT NULL | 表示順 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時（自動） |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時（自動） |

## インデックス

| インデックス名 | カラム | ユニーク |
|--------------|--------|---------|
| `ix_markets_market_code` | `market_code` | ✅ |
| `ix_markets_market_category` | `market_category` | ❌ |

## 登録データ（6件）

| market_code | market_category | market_name |
|------------|----------------|-------------|
| 0111 | PRIME | プライム（内国株式） |
| 0112 | STANDARD | スタンダード（内国株式） |
| 0113 | GROWTH | グロース（内国株式） |
| 0121 | PRIME | プライム（外国株式） |
| 0122 | STANDARD | スタンダード（外国株式） |
| 0123 | GROWTH | グロース（外国株式） |

## 関連テーブル

### このテーブルを参照するテーブル

- [`stock_master`](./stock_master.md) - 銘柄マスタ（`market_code`で紐付け）

## ソースコード

### Alembicマイグレーション

- [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L26-L82)

### SQLAlchemyモデル

- TBD（未実装）

## 使用例

```sql
-- 全市場区分を取得
SELECT market_code, market_name, market_category
FROM markets
ORDER BY sort_order;

-- プライム市場のみ取得
SELECT *
FROM markets
WHERE market_category = 'PRIME';
```

## 更新履歴

- **2026-07-22**: 初版作成（Alembic migration）
