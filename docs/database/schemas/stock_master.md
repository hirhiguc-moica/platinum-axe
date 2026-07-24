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
| `sector17_code` | VARCHAR(10) | NULL | 17業種コード（sector17sへの外部キー） |
| `market_code` | VARCHAR(10) | NULL | 市場区分コード |
| `scale_category` | VARCHAR(50) | NULL | 規模区分（TOPIX分類、下記参照） |
| `margin_code` | VARCHAR(10) | NULL | 信用区分コード（下記参照） |
| `listing_date` | DATE | NULL | 上場日 |
| `delisting_date` | DATE | NULL | 上場廃止日 |
| `is_active` | BOOLEAN | NOT NULL | 上場中フラグ |
| `market_cap` | NUMERIC(15,2) | NULL | 時価総額（最新） |
| `is_nikkei225` | BOOLEAN | NOT NULL | 日経225組入銘柄フラグ |
| `is_topix` | BOOLEAN | NOT NULL | TOPIX組入銘柄フラグ |
| `is_topix_core30` | BOOLEAN | NOT NULL | TOPIX Core30組入銘柄フラグ |
| `is_jpx400` | BOOLEAN | NOT NULL | JPX日経400組入銘柄フラグ |
| `info_date` | DATE | NOT NULL | 情報適用年月日（APIのDateフィールド、更新判断に使用） |
| `fetched_at` | TIMESTAMP | NOT NULL | API取得日時 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## コード値の説明

### 信用区分コード（margin_code）

| コード | 名称 | 説明 |
|--------|------|------|
| 1 | 信用 | 制度信用取引対象 |
| 2 | 貸借 | 貸借取引対象（空売り可能） |
| 3 | その他 | その他（現物のみ等） |

### 規模区分（scale_category）

TOPIX（東証株価指数）構成銘柄の規模別分類。時価総額・流動性に基づく。

| 値 | 説明 | 銘柄数目安 |
|----|------|-----------|
| `TOPIX Core30` | 超大型株30 | 31銘柄 |
| `TOPIX Large70` | 大型株70 | 68銘柄 |
| `TOPIX Mid400` | 中型株400 | 393銘柄 |
| `TOPIX Small 1` | 小型株1 | 484銘柄 |
| `TOPIX Small 2` | 小型株2 | 660銘柄 |
| `NULL` または `-` | TOPIX非構成銘柄 | 約2,800銘柄 |

## インデックス

- `ix_stock_master_stock_code` (stock_code) - UNIQUE
- `ix_stock_master_is_active` (is_active)
- `ix_stock_master_is_nikkei225` (is_nikkei225)
- `ix_stock_master_is_topix` (is_topix)
- `ix_stock_master_sector17_code` (sector17_code)

## 登録データ

- **現在**: 10銘柄（モックデータ）
- **本番**: 全銘柄（約4400銘柄、ETF・REIT含む）
  - 内国株券のみ: 約3800銘柄（想定）

## 関連テーブル

### 参照先
- [`markets`](./markets.md) - 市場区分マスタ
- [`sectors`](./sectors.md) - 33業種マスタ
- [`sector17s`](./sector17s.md) - 17業種マスタ

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
