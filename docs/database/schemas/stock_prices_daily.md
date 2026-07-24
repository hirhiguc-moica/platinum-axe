# stock_prices_daily（株価日次データ）

## 概要

全上場銘柄の日次株価データ（OHLC + 出来高）

## データソース

- **API**: `/v2/equities/bars/daily`
- **更新頻度**: 日次（営業日）
- **API更新時刻**: 17:30頃
- **Layer**: Layer 1 (Raw Data - J-Quants API)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `stock_code` | VARCHAR(10) | NOT NULL | 銘柄コード |
| `date` | DATE | NOT NULL | 日付 |
| `open` | NUMERIC(10,2) | NULL | 始値 |
| `high` | NUMERIC(10,2) | NULL | 高値 |
| `low` | NUMERIC(10,2) | NULL | 安値 |
| `close` | NUMERIC(10,2) | NULL | 終値 |
| `volume` | INTEGER | NULL | 出来高 |
| `turnover_value` | NUMERIC(15,2) | NULL | 売買代金 |
| `adjusted_open` | NUMERIC(10,2) | NULL | 調整後始値 |
| `adjusted_high` | NUMERIC(10,2) | NULL | 調整後高値 |
| `adjusted_low` | NUMERIC(10,2) | NULL | 調整後安値 |
| `adjusted_close` | NUMERIC(10,2) | NULL | 調整後終値 |
| `adjusted_volume` | INTEGER | NULL | 調整後出来高 |
| `adjustment_factor` | NUMERIC(10,6) | NULL | 調整係数（株式分割等） |
| `is_upper_limit` | BOOLEAN | NOT NULL | ストップ高フラグ |
| `is_lower_limit` | BOOLEAN | NOT NULL | ストップ安フラグ |
| `fetched_at` | TIMESTAMP | NOT NULL | API取得日時 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `idx_stock_prices_daily_code_date` (stock_code, date) - BTREE
- `idx_stock_prices_daily_date` (date) - BTREE

## 登録データ

- **現在**: トヨタ自動車（7203）240日分
- **本番**: 全銘柄（約3800銘柄）× 10年分（約2500営業日）

## 関連テーブル

### このテーブルから生成されるテーブル
- [`technical_indicators`](./technical_indicators.md) - テクニカル指標（125項目）を計算

### 参照先
- [`stock_master`](./stock_master.md) - 銘柄マスタ
- [`trading_calendar`](./trading_calendar.md) - 取引カレンダー（営業日判定）

## ソースコード

- **Alembic**: [20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py](../../../backend/alembic/versions/20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py#L25-L96)

## データ更新バッチ

- **初回全件取得**: TBD（未実装） - `backend/jobs/collectors/initialize_historical_data.py`
- **日次差分取得**: TBD（未実装） - `backend/jobs/collectors/collect_daily_data.py`

## 使用例

```sql
-- トヨタの直近240営業日の株価取得
SELECT date, close, volume
FROM stock_prices_daily
WHERE stock_code = '7203'
ORDER BY date DESC
LIMIT 240;

-- 特定日の全銘柄の株価取得
SELECT stock_code, close, volume
FROM stock_prices_daily
WHERE date = '2025-01-15';
```
