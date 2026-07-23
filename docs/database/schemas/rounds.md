# rounds（ラウンド管理）

## 概要

週次ラウンド情報（買い推奨 / 売り推奨）

## データソース

- **生成方法**: 機械学習モデルによる予測結果から生成
- **更新頻度**: 週次（土曜日）
- **Layer**: Layer 4 (Prediction & Result)

## スキーマ

| カラム | 型 | NULL | 説明 |
|--------|---|------|------|
| `id` | UUID | NOT NULL | 主キー |
| `round_id` | VARCHAR(20) | NOT NULL | ラウンドID（ビジネスキー、例: "2025-W03-BUY"） |
| `round_type` | VARCHAR(10) | NOT NULL | BUY / SELL |
| `start_date` | DATE | NOT NULL | 開始日（月曜） |
| `end_date` | DATE | NOT NULL | 終了日（金曜） |
| `status` | VARCHAR(20) | NOT NULL | ACTIVE / CLOSED |
| `model_version` | VARCHAR(20) | NULL | 使用したモデルバージョン |
| `feature_version` | VARCHAR(10) | NULL | 使用した特徴量バージョン |
| `prediction_date` | DATE | NULL | 予測実施日 |
| `created_at` | TIMESTAMP | NOT NULL | 作成日時 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新日時 |

## インデックス

- `ix_rounds_round_id` (round_id) - UNIQUE
- `ix_rounds_status` (status)

## 登録データ

- **現在**: 32件（モックデータ）
- **本番**: 週次で追加（買い・売りで2件/週）

## 関連テーブル

### このテーブルを参照するテーブル
- [`round_recommendations`](./round_recommendations.md) - 推奨銘柄（Top10）
- [`round_results`](./round_results.md) - ラウンド結果

## ソースコード

- **Alembic**: [20260722_1441_3e798dd4bfb9_initial_migration.py](../../../backend/alembic/versions/20260722_1441_3e798dd4bfb9_initial_migration.py#L83-L126)

## データ生成バッチ

- **週次予測**: TBD（未実装） - `backend/jobs/predictors/generate_weekly_predictions.py`
