# stock_master（銘柄マスタ）

## 概要

全上場銘柄の基本情報

## データソース

- **API**: `/v2/equities/master`
- **更新頻度**: 日次
- **Layer**: Layer 1 (Raw Data - J-Quants API)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `stock_code` | VARCHAR(10) | NOT NULL | 銘柄コード（ビジネスキー） |
| `company_name` | VARCHAR(255) | NOT NULL | 会社名 |
| `company_name_en` | VARCHAR(255) | NULL | 英語名 |
| `sector_code` | VARCHAR(10) | NULL | 業種コード（33業種分類） |
| `market_code` | VARCHAR(10) | NULL | 市場区分コード |
| `listing_date` | DATE | NULL | 上場日 |
| `delisting_date` | DATE | NULL | 上場廃止日 |
| `is_active` | BOOLEAN | NOT NULL | 上場中フラグ |
| `market_cap` | NUMERIC(15,2) | NULL | 時価総額（最新） |
| `is_nikkei225` | BOOLEAN | NOT NULL | 日経225組入銘柄フラグ |
| `is_topix` | BOOLEAN | NOT NULL | TOPIX組入銘柄フラグ |
| `is_topix_core30` | BOOLEAN | NOT NULL | TOPIX Core30組入銘柄フラグ |
| `is_jpx400` | BOOLEAN | NOT NULL | JPX日経400組入銘柄フラグ |
| `fetched_at` | TIMESTAMP | NOT NULL | API取得日時 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `ix_stock_master_stock_code` (stock_code) - UNIQUE
- `ix_stock_master_is_active` (is_active)
- `ix_stock_master_is_nikkei225` (is_nikkei225)
- `ix_stock_master_is_topix` (is_topix)

## 登録データ

- **現在**: 10銘柄（モックデータ）
- **本番**: 全銘柄（約3800銘柄）

## 関連テーブル

### 参照先
- [`markets`](./markets.md) - 市場区分マスタ
- [`sectors`](./sectors.md) - 業種マスタ

### このテーブルを参照するテーブル
- [`stock_prices_daily`](./stock_prices_daily.md) - 株価日次データ
- [`technical_indicators`](./technical_indicators.md) - テクニカル指標
- [`round_recommendations`](./round_recommendations.md) - 推奨銘柄
- [`round_results`](./round_results.md) - ラウンド結果

## ソースコード

- **Alembic**: [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L217-L269)

## データ更新バッチ

- **初回全件取得**: TBD（未実装）
- **日次更新**: TBD（未実装）
