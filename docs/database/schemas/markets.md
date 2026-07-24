# markets（市場区分マスタ）

## 概要

東京証券取引所の市場区分マスタデータ（Prime, Standard, Growth等）

## データソース

- **データ取得方法**: Alembicマイグレーション（自動投入）
- **データ元**: JPX（日本取引所グループ）公式コード
- **更新頻度**: 不定期（市場区分変更時のみ）
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

## 登録データ（10件）

### 新市場区分（2022年4月以降）

| market_code | market_category | market_name | 略号 |
|------------|----------------|-------------|-----|
| 0111 | PRIME | プライム | PR |
| 0112 | STANDARD | スタンダード | ST |
| 0113 | GROWTH | グロース | GR |

### 旧市場区分（2022年4月以前）

| market_code | market_category | market_name | 略号 |
|------------|----------------|-------------|-----|
| 0101 | LEGACY | 東証一部 | 東1 |
| 0102 | LEGACY | 東証二部 | 東2 |
| 0104 | LEGACY | マザーズ | MTH |
| 0106 | LEGACY | JASDAQ スタンダード | JQ-STD |
| 0107 | LEGACY | JASDAQ グロース | JQ-GRW |

### その他

| market_code | market_category | market_name | 略号 |
|------------|----------------|-------------|-----|
| 0105 | OTHER | TOKYO PRO MARKET | PRO |
| 0109 | OTHER | その他 | OTHER |

## 関連テーブル

### このテーブルを参照するテーブル

- [`stock_master`](./stock_master.md) - 銘柄マスタ（`market_code`で紐付け）

## ソースコード

### Alembicマイグレーション

- [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L26-L82) - テーブル作成
- [20260724_0200_b3c4d5e6f7g8_replace_markets_with_jpx_official_codes.py](../../../backend/alembic/versions/20260724_0200_b3c4d5e6f7g8_replace_markets_with_jpx_official_codes.py) - JPX公式コードで置き換え

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

- **2026-07-24**: JPX公式コードで置き換え（10件）
- **2026-07-22**: 初版作成（暫定データ6件）
