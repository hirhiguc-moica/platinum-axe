# プラチナの斧 - ドキュメント索引

このディレクトリには、プラチナの斧（platinum-axe）プロジェクトの設計ドキュメントが格納されています。

---

## 📚 ドキュメント一覧

### プロジェクト全体

| ドキュメント | 内容 |
|------------|------|
| [project-overview.md](./project-overview.md) | プロジェクト概要・目的・機能詳細 |
| [directory-structure.md](./directory-structure.md) | モノレポ構成・ディレクトリ配置ルール |

### アーキテクチャ

| ドキュメント | 内容 |
|------------|------|
| [architecture/system-architecture.md](./architecture/system-architecture.md) | システム全体アーキテクチャ・コンポーネント図 |
| [architecture/data-pipeline.md](./architecture/data-pipeline.md) | データパイプライン設計（データフロー） |
| [architecture/ml-workflow.md](./architecture/ml-workflow.md) | 機械学習ワークフロー（学習・推論） |

### データベース

| ドキュメント | 内容 |
|------------|------|
| [database/schemas.md](./database/schemas.md) | **全テーブル定義（最重要）** |
| [database/guidelines.md](./database/guidelines.md) | DB設計ガイドライン・命名規則 |

### Backend

| ドキュメント | 内容 |
|------------|------|
| [backend/structure.md](./backend/structure.md) | Backend DDD構造・層の責務 |
| [backend/coding-style.md](./backend/coding-style.md) | コーディング規約（Python/FastAPI） |
| [backend/development-guide.md](./backend/development-guide.md) | 開発手順・テスト方法 |
| [backend/api-specification.md](./backend/api-specification.md) | REST API仕様 |

### Frontend

| ドキュメント | 内容 |
|------------|------|
| [frontend/structure.md](./frontend/structure.md) | Frontend構造（Next.js/Turborepo） |
| [frontend/coding-style.md](./frontend/coding-style.md) | コーディング規約（TypeScript/React） |
| [frontend/environment.md](./frontend/environment.md) | 環境変数管理 |

### 機械学習

| ドキュメント | 内容 |
|------------|------|
| [ml/data-sources.md](./ml/data-sources.md) | データソース（J-Quants API詳細） |
| [ml/features.md](./ml/features.md) | **特徴量設計（重要）** |
| [ml/models.md](./ml/models.md) | モデル設計（LightGBM設定） |
| [ml/training-pipeline.md](./ml/training-pipeline.md) | 学習パイプライン・評価手法 |

### バッチ処理

| ドキュメント | 内容 |
|------------|------|
| [batch/data-collection.md](./batch/data-collection.md) | データ収集バッチ（J-Quants API取得） |
| [batch/preprocessing.md](./batch/preprocessing.md) | 前処理バッチ（テクニカル指標計算） |
| [batch/prediction.md](./batch/prediction.md) | 予測バッチ（ラウンド推奨・シグナル検出） |

### インフラストラクチャ

| ドキュメント | 内容 |
|------------|------|
| [infrastructure/local-development.md](./infrastructure/local-development.md) | ローカル開発環境（DevContainer） |
| [infrastructure/deployment.md](./infrastructure/deployment.md) | デプロイ手順（GCP） |
| [infrastructure/monitoring.md](./infrastructure/monitoring.md) | 監視・ログ設計 |

---

## 🚀 クイックスタート

### 新規参加者向け

1. **[../CLAUDE.md](../CLAUDE.md)** を読む
   - プロジェクト概要と作業ルールを理解

2. **[project-overview.md](./project-overview.md)** を読む
   - システムの目的と機能詳細を理解

3. **[directory-structure.md](./directory-structure.md)** を読む
   - コードベースの構造を理解

4. **担当領域のドキュメントを読む**
   - Backend担当 → `backend/`
   - Frontend担当 → `frontend/`
   - ML担当 → `ml/` + `batch/`

### 実装前の必須確認

| 実装内容 | 確認すべきドキュメント |
|---------|---------------------|
| **新機能追加（Backend）** | `backend/structure.md`, `backend/development-guide.md` |
| **DB変更・テーブル追加** | `database/schemas.md`, `database/guidelines.md` |
| **機械学習モデル変更** | `ml/features.md`, `ml/models.md` |
| **バッチ処理追加** | `batch/` + `architecture/data-pipeline.md` |
| **API追加** | `backend/api-specification.md` |

---

## 📝 ドキュメント更新ルール

### 更新が必要なタイミング

- ✅ 新機能を追加した時
- ✅ アーキテクチャを変更した時
- ✅ テーブル定義を変更した時
- ✅ API仕様を変更した時
- ✅ 重要な設計判断をした時

### 更新方法

1. 該当ドキュメントを直接編集
2. 変更内容をコミットメッセージに記載
3. 関連ドキュメントも併せて更新

---

## 🎯 重要度マーキング

ドキュメントには以下のマーキングがあります：

- ⭐⭐⭐ **最重要** - 必ず読むべきドキュメント
- ⭐⭐ **重要** - 実装前に確認推奨
- ⭐ **参考** - 必要に応じて参照

### 最重要ドキュメント（⭐⭐⭐）

1. **[database/schemas.md](./database/schemas.md)** - 全テーブル定義
2. **[ml/features.md](./ml/features.md)** - 特徴量設計
3. **[backend/structure.md](./backend/structure.md)** - Backend構造
4. **[architecture/system-architecture.md](./architecture/system-architecture.md)** - システム全体像

---

## 📂 ドキュメント構造

```
docs/
├── README.md                          # このファイル（索引）
├── project-overview.md                # プロジェクト概要
├── directory-structure.md             # モノレポ構成
│
├── architecture/                      # アーキテクチャ設計
│   ├── system-architecture.md         # システム全体
│   ├── data-pipeline.md               # データパイプライン
│   └── ml-workflow.md                 # ML ワークフロー
│
├── backend/                           # Backend仕様
│   ├── structure.md                   # DDD構造
│   ├── coding-style.md                # コーディング規約
│   ├── development-guide.md           # 開発手順
│   └── api-specification.md           # API仕様
│
├── frontend/                          # Frontend仕様
│   ├── structure.md                   # 構造
│   ├── coding-style.md                # コーディング規約
│   └── environment.md                 # 環境変数
│
├── ml/                                # 機械学習
│   ├── data-sources.md                # データソース
│   ├── features.md                    # 特徴量設計
│   ├── models.md                      # モデル設計
│   └── training-pipeline.md           # 学習パイプライン
│
├── batch/                             # バッチ処理
│   ├── data-collection.md             # データ収集
│   ├── preprocessing.md               # 前処理
│   └── prediction.md                  # 予測
│
├── database/                          # データベース
│   ├── schemas.md                     # テーブル定義
│   └── guidelines.md                  # 設計ガイドライン
│
└── infrastructure/                    # インフラ
    ├── local-development.md           # ローカル環境
    ├── deployment.md                  # デプロイ
    └── monitoring.md                  # 監視
```

---

## 🔍 ドキュメントの探し方

### 目的別

| やりたいこと | 参照ドキュメント |
|------------|----------------|
| プロジェクト全体を理解したい | `project-overview.md` |
| テーブルを追加したい | `database/schemas.md`, `database/guidelines.md` |
| APIを追加したい | `backend/api-specification.md`, `backend/development-guide.md` |
| 特徴量を追加したい | `ml/features.md` |
| バッチを追加したい | `batch/` + `architecture/data-pipeline.md` |
| 開発環境を構築したい | `infrastructure/local-development.md` |

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
