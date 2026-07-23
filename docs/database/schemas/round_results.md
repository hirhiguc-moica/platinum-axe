# round_results（ラウンド結果）

## 概要

各ラウンドの推奨銘柄の実績データ

## データソース

- **生成方法**: ラウンド終了後、[`stock_prices_daily`](./stock_prices_daily.md)から実績株価を取得して計算
- **更新頻度**: 週次（月曜朝、前週ラウンド結果確定時）
- **Layer**: Layer 4 (Prediction & Result)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `round_id` | UUID | NOT NULL | ラウンドID（UUID、外部キー） |
| `stock_code` | VARCHAR(10) | NOT NULL | 銘柄コード |
| `start_price` | NUMERIC(10,2) | NULL | 開始時点の株価（月曜始値） |
| `end_price` | NUMERIC(10,2) | NULL | 終了時点の株価（金曜終値） |
| `highest_price` | NUMERIC(10,2) | NULL | 期間中最高値 |
| `lowest_price` | NUMERIC(10,2) | NULL | 期間中最安値 |
| `actual_return` | NUMERIC(8,4) | NULL | 実際の騰落率（%） |
| `predicted_return` | NUMERIC(8,4) | NULL | 予測騰落率（%） |
| `prediction_error` | NUMERIC(8,4) | NULL | 予測誤差（actual - predicted） |
| `prediction_hit` | BOOLEAN | NULL | 予測が当たったか（方向性一致） |
| `entry_shares` | INTEGER | NOT NULL | 仮想投資株数 |
| `profit_loss` | NUMERIC(10,2) | NULL | 損益金額（円） |
| `profit_loss_rate` | NUMERIC(8,4) | NULL | 損益率（%） |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `idx_round_results_code` (stock_code) - BTREE
- `idx_round_results_round` (round_id) - BTREE

## 外部キー制約

- `round_id` → [`rounds`](./rounds.md) (`id`)

## 登録データ

- **現在**: 300件（モックデータ）
- **本番**: 週次で追加（買い10銘柄 + 売り10銘柄 = 20件/週）

## 関連テーブル

### 参照先
- [`rounds`](./rounds.md) - ラウンド管理
- [`stock_master`](./stock_master.md) - 銘柄マスタ
- [`stock_prices_daily`](./stock_prices_daily.md) - 実績株価の取得元

## ソースコード

- **Alembic**: [20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py](../../../backend/alembic/versions/20260722_1743_db42c44b1ad6_add_stock_prices_technical_indicators_.py#L584-L668)

## データ生成バッチ

- **週次結果計算**: TBD（未実装） - `backend/jobs/predictors/calculate_round_results.py`

## 使用例

```sql
-- 特定ラウンドの結果一覧（勝率計算）
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN prediction_hit = TRUE THEN 1 ELSE 0 END) AS hits,
    ROUND(SUM(CASE WHEN prediction_hit = TRUE THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS win_rate,
    AVG(actual_return) AS avg_return
FROM round_results
WHERE round_id = '...';
```
