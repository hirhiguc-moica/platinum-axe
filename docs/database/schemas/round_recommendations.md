# round_recommendations（ラウンド推奨銘柄）

## 概要

各ラウンドの推奨銘柄（買い/売り Top10）

## データソース

- **生成方法**: 機械学習モデルの予測結果から上位10銘柄を抽出
- **更新頻度**: 週次（土曜日）
- **Layer**: Layer 4 (Prediction & Result)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `round_id` | UUID | NOT NULL | ラウンドID（UUID、外部キー） |
| `stock_code` | VARCHAR(10) | NOT NULL | 銘柄コード |
| `rank` | INTEGER | NOT NULL | 推奨順位（1〜10位） |
| `predicted_return` | NUMERIC(8,4) | NULL | 予測騰落率（%） |
| `confidence_score` | NUMERIC(5,4) | NULL | 信頼度スコア（0〜1） |
| `reason_features` | JSONB | NULL | 推奨理由となった特徴量（JSON） |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `ix_round_recommendations_round_id` (round_id)

## 外部キー制約

- `round_id` → [`rounds`](./rounds.md) (`id`)

## 登録データ

- **現在**: 320件（モックデータ、32ラウンド × 10銘柄）
- **本番**: 週次で追加（買い10銘柄 + 売り10銘柄 = 20銘柄/週）

## 関連テーブル

### 参照先
- [`rounds`](./rounds.md) - ラウンド管理
- [`stock_master`](./stock_master.md) - 銘柄マスタ

## ソースコード

- **Alembic**: [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L160-L216)

## 使用例

```sql
-- 特定ラウンドの推奨銘柄Top10を取得
SELECT rr.rank, rr.stock_code, sm.company_name, rr.predicted_return
FROM round_recommendations rr
JOIN stock_master sm ON rr.stock_code = sm.stock_code
WHERE rr.round_id = '...'
ORDER BY rr.rank;
```
