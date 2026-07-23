# technical_indicators（テクニカル指標）

## 概要

株価データから計算した125種類のテクニカル指標

## データソース

- **計算元**: [`stock_prices_daily`](./stock_prices_daily.md)
- **更新頻度**: 日次（株価データ更新後）
- **Layer**: Layer 2 (Derived Data - 計算で生成)

## スキーマ

### 主要カラム

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `stock_code` | VARCHAR(10) | NOT NULL | 銘柄コード |
| `date` | DATE | NOT NULL | 日付 |
| **トレンド系（移動平均等）** | | | |
| `ma_5` | NUMERIC(10,2) | NULL | 5日移動平均 |
| `ma_25` | NUMERIC(10,2) | NULL | 25日移動平均 |
| `ma_75` | NUMERIC(10,2) | NULL | 75日移動平均 |
| `ema_12` | NUMERIC(10,2) | NULL | 12日指数移動平均 |
| `macd` | NUMERIC(10,4) | NULL | MACD |
| `macd_signal` | NUMERIC(10,4) | NULL | MACDシグナル |
| **オシレーター系** | | | |
| `rsi_14` | NUMERIC(5,2) | NULL | RSI（14日） |
| `stoch_k` | NUMERIC(5,2) | NULL | ストキャスティクス%K |
| `cci_20` | NUMERIC(10,4) | NULL | CCI（20日） |
| **ボラティリティ系** | | | |
| `bb_upper` | NUMERIC(10,2) | NULL | ボリンジャーバンド上限 |
| `bb_lower` | NUMERIC(10,2) | NULL | ボリンジャーバンド下限 |
| `atr_14` | NUMERIC(10,2) | NULL | ATR（14日） |
| **出来高系** | | | |
| `volume_ma_20` | INTEGER | NULL | 出来高20日移動平均 |
| `obv` | BIGINT | NULL | OBV |
| `calculated_at` | TIMESTAMP | NOT NULL | 計算実行日時 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

### 全125項目の詳細

全カラムの詳細定義は以下を参照：
- [Alembicマイグレーションファイル](../../../backend/alembic/versions/20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py#L97-L579)

## インデックス

- `idx_technical_indicators_code_date` (stock_code, date) - BTREE
- `idx_technical_indicators_date` (date) - BTREE

## 登録データ

- **現在**: トヨタ自動車（7203）240日分、125項目
- **本番**: 全銘柄（約3800銘柄）× 10年分（約2500営業日）× 125項目

## 関連テーブル

### 計算元テーブル
- [`stock_prices_daily`](./stock_prices_daily.md) - 株価日次データ

### このテーブルから生成されるテーブル
- `ml_features` - 機械学習用特徴量（未実装）

## ソースコード

- **Alembic**: [20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py](../../../backend/alembic/versions/20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py#L97-L579)

## データ更新バッチ

- **初回全件計算**: TBD（未実装） - 株価データ取得後に実行
- **日次追加計算**: TBD（未実装） - `backend/jobs/preprocessors/calculate_technical_indicators.py`
