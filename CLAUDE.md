# Claude Code 作業ルール - プラチナの斧（platinum-axe）

## 概要

**プロジェクト名**: プラチナの斧（platinum-axe）

J-Quants APIを活用した機械学習による**日本株銘柄推奨システム**。

**目的**:

- 個人投資家向けの投資判断支援ツール
- 機械学習（勾配ブースティング）による定量分析
- 推奨銘柄のパフォーマンス追跡
- 将来的にGCP上に公開予定

**特徴**:

- ✅ 週次ラウンド制（買い推奨 / 売り推奨 各Top10）
- ✅ デイリー強シグナル検出（緊急買い/売り）
- ✅ J-Quants API Standardプラン（10年データ + 信用取引データ）
- ✅ LightGBM（勾配ブースティング）による予測
- ✅ トランザクションデータ保存 + テクニカル指標事前計算

---

## プロジェクト構成

### モノレポ構成

```
platinum-axe/
├── frontend/                    # Web UI
│   ├── apps/
│   │   └── web-main/           # メインアプリ（推奨銘柄表示）
│   └── packages/
│       ├── ui/                 # 共通UIコンポーネント
│       └── shared/             # 型定義
│
├── backend/                     # FastAPI（REST API）
│   └── app/
│       ├── domain/             # ドメインロジック
│       ├── usecase/            # ユースケース
│       ├── infrastructure/     # DB・外部API連携
│       └── presentation/api/v1/
│           ├── rounds/         # ラウンド管理API
│           ├── recommendations/# 推奨銘柄API
│           ├── signals/        # デイリーシグナルAPI
│           └── stocks/         # 銘柄情報API
│
├── ml/                          # 機械学習
│   ├── notebooks/              # Jupyter Notebook（分析）
│   ├── features/               # 特徴量エンジニアリング
│   ├── models/                 # モデル学習・保存
│   ├── evaluation/             # モデル評価
│   └── prediction/             # 推論スクリプト
│
└── batch/                       # バッチ処理
    ├── data_collection/        # J-Quants APIからデータ収集
    ├── preprocessing/          # 特徴量計算
    ├── model_training/         # モデル再学習
    ├── weekly_prediction/      # 週次推奨銘柄生成
    ├── daily_signal/           # デイリーシグナル検出
    └── result_verification/    # 結果検証
```

---

## システムの核心機能

### 1. 週次ラウンド制

**ラウンド = 1週間の推奨サイクル**

```
【ラウンドN】月曜〜金曜
├─ 買い推奨: 今週上昇予測の Top 10銘柄
└─ 売り推奨: 今週下落予測の Top 10銘柄

【翌週月曜】
└─ ラウンドNの結果検証 → パフォーマンス計算
```

### 2. デイリー強シグナル

**毎営業日17:30以降に検出**

- 強い買いシグナル: 予測騰落率 > +5%（閾値調整可）
- 強い売りシグナル: 予測騰落率 < -5%
- 信頼度スコア > 80%

### 3. 機械学習モデル

- **アルゴリズム**: LightGBM（勾配ブースティング）
- **予測ターゲット**: 翌週の騰落率（回帰）
- **特徴量**:
  - ファンダメンタル（PER, PBR, ROE, 売上成長率等）
  - テクニカル（移動平均, RSI, MACD, ボリンジャー等）
  - 市場センチメント（信用取引残高, 空売り比率等）
  - マクロ経済（TOPIX, セクター騰落率等）

---

## データソース: J-Quants API

### 契約プラン

- **プラン**: Standardプラン（¥3,300/月）
- **データ期間**: 過去10年分
- **選定理由**:
  - 基本的な株価・財務・信用取引データが揃っている
  - コスト効率が良い（Premium比で年間¥158,400節約）
  - Standard→Premium移行は容易（データ互換性あり）
  - まずStandardで実装・検証し、必要に応じてアップグレード可能

### データ更新タイミング

| 時刻 | 内容 |
|------|------|
| **17:30頃** | 当日取引終了後、株価四本値・信用取引データ等が更新 |
| **翌営業日 8:00頃** | 追加データ更新・確定データ配信 |

### 取得データ一覧（Standardプラン）

**基本データ**:
- ✅ 株価四本値（OHLC、調整済み株価）
- ✅ 財務情報（PER, PBR, ROE, EPS, BPS等のサマリー指標）
- ✅ 信用取引データ（日々公表残高含む）
- ✅ 指数データ（TOPIX含む）
- ✅ 日経225OP四本値データ
- ✅ 上場銘柄マスタ

**Premium限定データ（将来的に追加検討）**:
- ⏳ 財務諸表詳細（売上、営業利益、キャッシュフロー等）
- ⏳ 先物OP四本値データ
- ⏳ 配当金データ
- ⏳ 売買内訳データ（投資部門別売買動向）

---

## データベース設計方針

### データレイヤー構造

```
【Layer 1】Raw Data（トランザクションデータ）
  └─ J-Quants APIから取得した生データをそのまま保存
     - stock_prices_daily（株価四本値）
     - financial_statements（財務諸表）
     - margin_trading_daily（信用取引日次）
     - margin_trading_weekly（信用取引週次）
     - market_sentiment（空売り比率等）
     - stock_master（銘柄マスタ）

【Layer 2】Derived Data（計算済みデータ）
  └─ テクニカル指標を事前計算してDB保存
     - technical_indicators（MA, RSI, MACD, ボリンジャー等）

【Layer 3】Feature Store（機械学習用特徴量）
  └─ モデル学習・推論用に最適化されたデータ
     - ml_features（全特徴量をJSONB形式で保存）

【Layer 4】Prediction & Result（予測・結果）
  └─ ラウンド推奨・デイリーシグナル・実績データ
     - rounds（ラウンド管理）
     - round_recommendations（推奨銘柄）
     - round_results（結果検証）
     - daily_signals（デイリーシグナル）
```

### 設計の利点

- 📝 **トランザクションデータ保存**: APIデータの履歴追跡可能
- 🔄 **再計算可能**: バグ修正時に過去データの再処理ができる
- ⚡ **高速推論**: テクニカル指標を事前計算（毎回計算不要）
- 📊 **監査可能**: データ品質チェック・可視化が容易

---

## 週次ワークフロー

```
【毎営業日 17:30〜18:00】
└─ Batch: J-Quants APIから株価・財務・信用取引データ取得
   └─ DB保存: Layer 1（Raw Data）

【毎営業日 18:00〜18:30】
├─ Batch: テクニカル指標計算
│   └─ DB保存: Layer 2（technical_indicators）
└─ Batch: 機械学習特徴量生成
    └─ DB保存: Layer 3（ml_features）

【毎営業日 18:30〜19:00】
└─ Batch: デイリーシグナル検出
    └─ DB保存: daily_signals

【週末（土曜朝）】
├─ Batch: 今週のラウンド結果検証
│   └─ DB保存: round_results
└─ Batch: 来週のラウンド推奨銘柄算出
    ├─ 買い推奨 Top 10
    ├─ 売り推奨 Top 10
    └─ DB保存: rounds, round_recommendations

【月曜朝】
└─ Frontend: 新ラウンド開始・推奨銘柄表示
```

---

## 技術スタック

**参考プロジェクト**: jobsan (`/Users/hh/dev/github/jobsan`) のFE/BE構成を踏襲

### Backend
- **Python 3.12** + **uv** (パッケージマネージャー)
- **FastAPI** (REST API + OpenAPI自動生成)
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (DBマイグレーション)
- **PostgreSQL 15** (データベース)
- **Redis** (キャッシュ・セッション管理)
- **DDD構造** (domain/usecase/infrastructure/presentation)

### Frontend
- **Node.js 22** + **pnpm** (パッケージマネージャー)
- **Next.js 15** (App Router)
- **React 19**
- **TypeScript**
- **TanStack Query** (データフェッチング・キャッシング)
- **@hey-api/openapi-ts** (Backend API型自動生成)
- **shadcn/ui** (UIコンポーネント)
- **Tailwind CSS v4** (スタイリング)
- ❌ **Turborepo不要** (アプリ1つのみ)

### 機械学習
- **Python 3.12**
- **LightGBM** (勾配ブースティング)
- **pandas, numpy, scikit-learn**
- **Jupyter Notebook** (分析・可視化)

### インフラ
- **VSCode DevContainer** (ローカル開発環境)
- **Docker / Docker Compose**
- **GCP** (将来的なデプロイ先)

---

## Claude Code 作業ルール

### 1. セッション開始時の必須確認事項

**必ず以下を確認してから作業を開始すること：**

1. **このCLAUDE.mdを読む** - プロジェクト概要と現在の作業状況を確認
2. **「現在の作業状況」セクションを確認** - 前回セッションの続きを把握
3. **「次のタスク」を確認** - 何をすべきか明確にする
4. **docs/を参照する** - 実装方針・アーキテクチャを確認

### 2. ファイル変更時の原則

**必ず開発者と合意してからファイル変更を行うこと**

- ファイルの作成・編集・削除を行う前に、必ず開発者に内容を提示し、承認を得る
- 提案内容を明確に説明し、変更の目的と影響範囲を伝える
- 開発者が承認した後にのみ、実際のファイル操作を実行する
- 緊急性の高い修正であっても、事前確認を省略しない

### 3. CLAUDE.md の継続的な更新（重要）

**セッション中断に備えて、CLAUDE.mdを都度更新すること**

- 作業が一区切りついたら、**必ず CLAUDE.md の「現在の作業状況」を更新する**
- セッションが切断されても、次回スムーズに再開できるようにする
- 更新内容：
  - ✅ 完了したタスクを記録
  - 📝 実装内容（作成ファイル、変更内容等）
  - 🔄 次のタスクを明確に記載
  - 📅 最終更新日時を更新

### 4. docs/の内容に準拠すること（最重要）

**実装時は必ずdocs/の内容に従うこと：**

- 不明な点があれば、まずdocs/を確認
- docs/に記載がない場合は開発者に質問
- **推測で実装しない**

### 5. 禁止事項（許可なく実行しないこと）

以下の操作は**開発者の明示的な許可がない限り実行禁止**：

#### Database操作

- ❌ `alembic upgrade/downgrade` - マイグレーション実行
- ❌ `alembic revision` - マイグレーションファイル作成（コード生成はOK、実行は禁止）
- ❌ データベースへの直接接続・クエリ実行
- ❌ シードデータの投入

#### Git操作

- ❌ `git commit` - コミット作成
- ❌ `git push` - リモートへのプッシュ
- ❌ `git merge/rebase` - ブランチ操作
- ❌ `.gitignore`の変更（追加は相談後に実施）

#### 環境・設定ファイル

- ❌ `.env`ファイルの作成・編集（`.env.example`はOK）
- ❌ `pyproject.toml`の依存関係変更（相談後に実施）
- ❌ `package.json`の依存関係変更（相談後に実施）
- ❌ DevContainer設定の変更（`.devcontainer/`）

#### 破壊的操作

- ❌ ファイルの削除（リファクタリング時も事前相談）
- ❌ ディレクトリ構造の大幅な変更
- ❌ 本番環境への操作（絶対禁止）

### 6. 推奨される作業フロー

```
1. CLAUDE.mdを確認
   ↓
2. docs/で実装方針を確認
   ↓
3. 実装計画を開発者に提示
   ↓
4. 承認を得る
   ↓
5. 実装を進める
   ↓
6. テストを実行
   ↓
7. CLAUDE.mdを更新
```

### 7. 質問・相談のタイミング

以下の場合は必ず開発者に相談すること：

- docs/に記載がない実装方法を選択する必要がある場合
- ディレクトリ構造に疑問がある場合
- 既存のコードとdocs/の内容が矛盾している場合
- 複数の実装方法があり、どれが最適か判断できない場合
- 大規模なリファクタリングが必要な場合

---

## ドキュメント構成

詳細な仕様・設計は全て`docs/`配下に集約されています：

```
docs/
├── README.md                          # ドキュメント索引
├── project-overview.md                # プロジェクト概要（詳細版）
├── directory-structure.md             # モノレポ構成詳細
├── architecture/
│   ├── system-architecture.md         # システム全体アーキテクチャ
│   ├── data-pipeline.md               # データパイプライン設計
│   └── ml-workflow.md                 # 機械学習ワークフロー
├── backend/
│   ├── structure.md                   # Backend DDD構造
│   ├── coding-style.md                # コーディング規約
│   ├── development-guide.md           # 開発手順
│   └── api-specification.md           # API仕様
├── frontend/
│   ├── structure.md                   # Frontend構造
│   ├── coding-style.md                # コーディング規約
│   └── environment.md                 # 環境変数管理
├── ml/                                # 機械学習関連
│   ├── data-sources.md                # データソース（J-Quants API）
│   ├── features.md                    # 特徴量設計
│   ├── models.md                      # モデル設計
│   └── training-pipeline.md           # 学習パイプライン
├── batch/                             # バッチ処理
│   ├── data-collection.md             # データ収集バッチ
│   ├── preprocessing.md               # 前処理バッチ
│   └── prediction.md                  # 予測バッチ
├── database/
│   ├── guidelines.md                  # DB設計ガイドライン
│   └── schemas.md                     # テーブル定義（詳細）
└── infrastructure/
    ├── local-development.md           # ローカル開発環境（DevContainer）
    ├── deployment.md                  # デプロイ手順
    └── monitoring.md                  # 監視・ログ設計
```

---

## 現在の作業状況

### 完了したタスク

✅ **2026-07-21 午前**: プロジェクト概要の整理・確定
  - システムの核心機能を決定（週次ラウンド + デイリーシグナル）
  - J-Quants API Standardプラン + 信用取引データを確定
  - 機械学習手法を決定（LightGBM / 勾配ブースティング）
  - データベース設計方針を策定（4層レイヤー構造）
  - モノレポ構成を決定（frontend/backend/ml/batch）
  - 週次ワークフローを設計

✅ **2026-07-21 午前**: CLAUDE.md作成
  - プロジェクト概要
  - システムアーキテクチャ概要
  - データベース設計方針
  - 作業ルール

✅ **2026-07-21 午前**: ドキュメント基盤の構築
  - docs/ディレクトリ構造作成
  - docs/README.md作成（ドキュメント索引）
  - docs/database/schemas.md作成（全テーブル定義24テーブル）

✅ **2026-07-21 午前**: 技術スタック確定
  - jobsan構成を確認・踏襲
  - FE: Next.js 15 + TanStack Query + shadcn/ui + Tailwind CSS v4
  - BE: FastAPI + SQLAlchemy 2.0 + Alembic + DDD構造
  - OpenAPI経由での型自動生成フロー確定

✅ **2026-07-21 午前**: 実装設計ドキュメント完成
  - docs/directory-structure.md作成（モノレポ全体構成）
  - docs/backend/structure.md作成（DDD 4層アーキテクチャ詳細）
  - docs/frontend/structure.md作成（shadcn/ui中心のUI設計）
  - 認証なし方針確定（将来的にFirebase Auth導入予定）
  - ページ構成確定（ホーム/今週の予測/過去の結果/銘柄詳細）

✅ **2026-07-21 午後**: DevContainer設定完成
  - .devcontainer/Dockerfile作成（Python 3.12 + Node.js 22 + uv + pnpm）
  - .devcontainer/docker-compose.yml作成（app + db + redis）
  - .devcontainer/devcontainer.json作成（VSCode設定）

✅ **2026-07-21 午後**: Backend初期ファイル雛形作成
  - backend/pyproject.toml作成（依存関係定義）
  - backend/app/shared/config.py作成（Pydantic Settings）
  - backend/app/main.py作成（FastAPIアプリケーション）

✅ **2026-07-21 午後**: ドキュメント完成（全て完了）
  - docs/project-overview.md作成（プロジェクト概要詳細版）
  - docs/frontend/user-guide.md作成（⭐ 一般ユーザー向け「使い方」ページ）
  - docs/infrastructure/local-development.md作成（DevContainer使い方）
  - docs/backend/coding-style.md作成（コーディング規約）
  - docs/frontend/coding-style.md作成（コーディング規約）
  - docs/database/guidelines.md作成（DB設計ガイドライン）

✅ **2026-07-22 午前**: DevContainer環境構築 + 疎通確認完了
  - DevContainer設定修正（Dockerfile, devcontainer.json, docker-compose.yml）
  - Docker環境起動確認（app, db, redis）
  - Backend依存関係インストール完了（155パッケージ）
  - Frontend依存関係インストール完了（312パッケージ）
  - PostgreSQL/Redis接続確認成功
  - Backend Health Check API実装（/api/v1/health）
  - Frontend最小限ページ実装（疎通確認UI付き）
  - CORS設定完了（config.py修正）
  - Backend起動確認（http://localhost:8000）
  - Frontend起動確認（http://localhost:3000）
  - FE⇄BE API疎通確認成功 🎉

✅ **2026-07-22 深夜**: データベース設計見直し + Alembicセットアップ完了
  - J-Quants API Standardプラン選定確認（¥3,300/月）
  - **データベース設計見直し（UUID主キー導入）**
    - 全テーブルにUUID主キー（`id`）+ マジックカラム（`created_at`, `updated_at`）追加
    - ビジネスキー（`stock_code`, `round_id`）はUNIQUE制約として維持
    - `TimestampMixin`パターン実装（`@declared_attr`使用）
    - サーバーサイドデフォルト設定（`gen_random_uuid()`, `CURRENT_TIMESTAMP`）
  - **Alembicセットアップ完了**
    - `backend/alembic.ini`作成（東京タイムゾーン、Ruff連携）
    - `backend/alembic/env.py`作成（async対応、autogenerate対応）
  - **ドメインモデル作成**
    - `app/domain/models/base.py`（Base, TimestampMixin）
    - `app/domain/models/stock.py`（StockMaster）
    - `app/domain/models/round.py`（Round, RoundRecommendation）
  - **初回マイグレーション実行成功**
    - `alembic revision --autogenerate`実行
    - `alembic upgrade head`実行
    - 3テーブル作成成功（`stock_master`, `rounds`, `round_recommendations`）
  - **モックデータ投入成功**
    - `backend/scripts/seed_mock_data.py`作成
    - 銘柄マスタ10件（トヨタ、ソニー、SoftBank等）
    - ラウンド2件（2026-W30-BUY / SELL）
    - 推奨銘柄10件（BUY Top5, SELL Top5）
    - UUID外部キー関連付け成功 🎉

### 📂 作成済みファイル（2026-07-22）

**Backend - 環境設定**:
- `backend/.env` / `backend/.env.example`
- `backend/app/shared/config.py`（CORS設定追加）
- `backend/app/main.py`（Health Check API登録、CORS設定修正）
- `backend/app/presentation/api/v1/health.py`（Health Check API）

**Backend - データベース関連**:
- `backend/alembic.ini`（Alembic設定、東京タイムゾーン）
- `backend/alembic/env.py`（async対応、autogenerate対応）
- `backend/alembic/versions/xxxxx_initial_migration.py`（初回マイグレーション）
- `backend/app/domain/models/base.py`（Base, TimestampMixin）
- `backend/app/domain/models/stock.py`（StockMaster）
- `backend/app/domain/models/round.py`（Round, RoundRecommendation）
- `backend/app/domain/models/__init__.py`
- `backend/app/infrastructure/database.py`（DB接続管理）
- `backend/app/infrastructure/repositories/round_repository.py`（RoundRepository, RoundRecommendationRepository）
- `backend/scripts/seed_mock_data.py`（モックデータ投入スクリプト）

**Frontend**:
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/next.config.ts`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`（疎通確認UI）

**DevContainer修正**:
- `.devcontainer/Dockerfile`（uvのPATH修正）
- `.devcontainer/devcontainer.json`（postCreateCommand修正）
- `.devcontainer/docker-compose.yml`（version削除）

✅ **2026-07-22 午後〜夜**: Backend API実装完了
  - **Repository層修正**
    - `RoundRecommendationRepository.find_by_round_uuid(round_uuid: UUID)` 実装
    - selectinload でstock情報をJOIN取得
  - **UseCase層実装**
    - `GetRoundsUseCase`（全ラウンド取得）
    - `GetRoundRecommendationsUseCase`（ビジネスキー→UUID変換含む）
  - **API実装**
    - `GET /api/v1/rounds`（全ラウンド一覧）
    - `GET /api/v1/rounds/{round_id}/recommendations`（推奨銘柄取得）
    - Swagger UI動作確認成功（http://localhost:8000/docs）

✅ **2026-07-22 夜**: Frontend OpenAPI型生成 + SSR実装
  - OpenAPI JSON生成成功
  - @hey-api/openapi-ts設定完了
  - TypeScript型生成成功
  - SSR実装（CSRから変更）
  - データ取得・表示確認成功
  - stock情報（company_name, sector_name, market_name）追加

✅ **2026-07-22 夜**: Tailwind CSS v4セットアップ
  - shadcn/ui依存関係追加
  - Tailwind CSS v4設定（tailwind.config.ts, postcss.config.js）
  - globals.css修正（@apply削除、直接CSSプロパティ指定）
  - components.json作成
  - lib/utils.ts作成（cn関数）

✅ **2026-07-22 深夜**: データベース再設計完了
  - **Sectorモデル作成**
    - 33業種分類マスタ（水産・農林業、化学、電気機器、情報・通信業等）
    - `backend/app/domain/models/sector.py`
    - `backend/scripts/seed_sectors.py`
  - **Marketモデル作成**
    - 市場区分マスタ（PRIME/STANDARD/GROWTH + 内国/外国）
    - market_code: PRIME, STANDARD, GROWTH, PRIME_F, STANDARD_F, GROWTH_F
    - market_abbreviation: PR, ST, GR
    - `backend/app/domain/models/market.py`
    - `backend/scripts/seed_markets.py`
  - **StockMaster拡張**
    - sector_code外部キー追加（sectors.sector_code）
    - market_code外部キー追加（markets.market_code）
    - market_name削除（正規化）
    - 指数フラグ追加（is_nikkei225, is_topix, is_topix_core30, is_jpx400）
    - sector/market relationship追加
  - **マイグレーション再実行**
    - DB完全リセット（reset_db.py, clean_alembic.py作成）
    - 初回マイグレーション再生成（initial_migration）
    - 5テーブル作成成功（markets, sectors, stock_master, rounds, round_recommendations）
  - **seedデータ投入完了**
    - 市場マスタ6件（PRIME/STANDARD/GROWTH × 内国/外国）
    - 業種マスタ33件
    - 銘柄マスタ10件（指数フラグ付き、sector/market外部キー設定）
    - ラウンド2件（BUY/SELL）
    - 推奨銘柄10件
  - **API動作確認成功**
    - sector_name正常表示（例: "輸送用機器", "電気機器", "情報・通信業"）
    - market_name正常表示（"プライム"）

✅ **2026-07-22 深夜**: Frontend UI実装完了
  - **shadcn/uiコンポーネント実装**
    - Header.tsx（ナビゲーション、アクティブリンク検出）
    - RankBadge.tsx（ランキングバッジ、1〜3位は特別デザイン）
    - RecommendationCard.tsx（推奨銘柄カード、信頼度プログレスバー付き）
    - FilterTabs.tsx（BUY/SELL切り替えタブ）
  - **ページ実装**
    - app/[filter]/page.tsx（メインページ、BUY/SELL両方表示）
    - app/[filter]/[type]/page.tsx（個別フィルタページ）
    - app/page.tsx（/all へリダイレクト）
  - **VSCode風ダークモード完成**
    - globals.css（Tailwind CSS v4対応、hsl()カラー定義）
    - グラデーション（gradient-buy, gradient-sell, gradient-gold）
    - カードホバーエフェクト（card-hover）
  - **情報アーキテクチャ改善**
    - 先週の実績を最上部に配置（信頼性訴求）
    - 説明セクション追加（システム理解促進）
    - 日付表示改善（曜日付き + 更新情報）
    - ビジネスコード非表示（round_id削除）
  - **日付表示UX改善**
    - formatDateRangeJa()関数実装（例: 7月20日（月）〜 7月24日（金））
    - getNextSaturday()関数実装（次回更新日計算）
    - ステータス表示追加（「ℹ️ 現在予測中 | 次回更新: X月X日（土）」）

✅ **2026-07-22 深夜**: Frontend UI最終調整・ネオン効果実装完了
  - **情報配置の最適化**
    - サイト説明（クオンツ × AI による週次スイング取引）を最上部に配置
    - ページタイトル（総合ランキング等）をその下に配置
    - 情報の流れを改善：説明 → タイトル → 実績 → 推奨銘柄
  - **予測期間カードの統合**
    - 買い推奨・売り推奨セクションに予測期間カードを統合
    - グラデーション背景（emerald/red）+ ネオンボーダー
    - 「現在予測中」パルスアニメーション + ネオングロー
  - **ネオン効果の実装**
    - セクションタイトル（📈 買い推奨 / 📉 売り推奨）にネオングロー
    - 先週の実績カードに色分けグラデーション背景
    - 数値（+3.2%, -2.8%）にネオングロー
    - 推奨銘柄カードの予測騰落率にネオングロー
    - メインタイトルにゴールドグラデーション
  - **クリック可能なUIデザイン**
    - カードにcursor-pointerとホバー拡大効果（scale-[1.02]）
    - ホバー時の浮き上がり効果強化（-4px）
    - ゴールドグロー追加
    - クリック時の押し込みエフェクト（:active）
  - **CSS実装**
    - neon-text-green / neon-text-red クラス
    - neon-text-sm クラス
    - neon-pulse アニメーション
    - card-hover 強化

✅ **2026-07-22 午後**: 銘柄詳細ページ向けBackend API実装完了
  - **テクニカル指標テーブル追加**
    - マイグレーション実行（125個の指標カラム追加）
    - `technical_indicators`テーブル作成（130カラム = 125指標 + 5メタデータ）
  - **モックデータ生成スクリプト作成**
    - `backend/scripts/seed_stock_prices.py`作成
    - トヨタ（7203）240日分の株価+テクニカル指標を生成
    - 期間: 2025-11-24 〜 2026-10-23
  - **カラム名不一致修正（73個）**
    - スクリプトとモデル間のカラム名を統一
    - Bollinger Bands, ADX/DI, Ichimoku, 価格位置指標等
    - `backend/scripts/check_column_names.py`作成（検証ツール）
  - **銘柄詳細API実装（4エンドポイント）**
    - GET /api/v1/stocks/{stock_code}（銘柄基本情報）
    - GET /api/v1/stocks/{stock_code}/prices（株価履歴）
    - GET /api/v1/stocks/{stock_code}/technical-indicators（主要14指標）
    - GET /api/v1/stocks/{stock_code}/recommendations（推奨履歴）
  - **テクニカル指標full版エンドポイント追加**
    - GET /api/v1/stocks/{stock_code}/technical-indicators/full（全125指標）
    - チャート描画・詳細分析向け
  - **動作確認完了**
    - 全エンドポイント動作確認済み（Swagger UI経由）
    - 240件のデータ取得成功、ページネーション正常動作

✅ **2026-07-22 夕方〜夜**: 銘柄詳細ページFrontend実装完了 🎉
  - **チャート機能実装**
    - TradingView Lightweight Charts v5.2.0導入
    - `app/stocks/[stock_code]/_components/StockChart.tsx`作成（チャートコンポーネント）
    - `app/stocks/[stock_code]/_components/StockDataTabs.tsx`作成（タブ切り替えUI）
    - `app/stocks/[stock_code]/page.tsx`修正（SSRでデータ取得）
  - **チャート機能詳細**
    - ローソク足チャート（240日分の四本値）
    - 移動平均線3本（MA5/MA25/MA75）オーバーレイ表示
    - 出来高ヒストグラム（下部に表示）
    - ダークモード対応（VSCode風カラースキーム）
    - レスポンシブ対応（ウィンドウリサイズ対応）
  - **lightweight-charts v5 API対応**
    - v5で変更されたAPIに対応（`addSeries()`メソッド使用）
    - `CandlestickSeries`, `LineSeries`, `HistogramSeries`のインポート追加
    - 型安全なチャート実装
  - **タブUI実装**
    - shadcn/ui Tabsコンポーネント使用
    - 3タブ構成：チャート / 株価データ / テクニカル指標
    - チャートタブをデフォルト表示
    - 株価データ・テクニカル指標テーブルにSticky Header適用
  - **銘柄詳細ページ完成**
    - 銘柄基本情報表示（会社名、業種、市場、指数バッジ）
    - 最新株価サマリー表示
    - チャート/テーブルタブ切り替え
    - 推奨履歴表示（予測 vs 実績）
    - RecommendationCardからのリンク接続完了

✅ **2026-07-22 夜**: 推奨履歴チャート機能実装 + UIブラッシュアップ 🎨
  - **コンポーネント配置整理**
    - `stocks/[stock_code]/_components/` ディレクトリ作成
    - `StockChart.tsx`, `StockDataTabs.tsx` を `_components/` に移動
    - 将来的に `stocks/_components/` への昇格が容易な構造
    - プライベートコンポーネントも整理することで共通化しやすく
  - **推奨履歴タブUI実装**
    - `RecommendationTabs.tsx` 作成（タブ切り替えUI）
    - `RecommendationAccuracyChart.tsx` 作成（折れ線グラフ）
    - タブ1: 予測 vs 実績チャート（デフォルト）
    - タブ2: 詳細リスト
  - **予測 vs 実績の折れ線グラフ実装**
    - TradingView Lightweight Charts使用
    - 青線：予測騰落率の推移
    - 橙線：実績騰落率の推移
    - 予測精度が一目でわかる可視化
    - 日付フォーマット：MM/dd形式（例: 07/20）
  - **UIブラッシュアップ**
    - 全セクションから件数表示を削除（「240件」等）
    - タイトルを簡素化（情報過多を解消）
    - よりシンプルで見やすいUIに改善

✅ **2026-07-22 夜**: Headerシステム説明バナー追加 + 銘柄詳細ページv1完成 🎉
  - **Headerにシステム説明バナー追加**
    - `app/_components/Header.tsx` 修正
    - バナーテキスト：「個人投資家に クオンツ分析 × AI によるデータ・ドリブンな株取引を」
    - 非sticky配置（スクロールすると消える）
    - グラデーション背景 + 「クオンツ分析 × AI」部分にグラデーションテキスト
    - メインヘッダーはstickyのまま維持
  - **ナビゲーション改善**
    - 「About」→「使い方」に変更
  - **銘柄詳細ページv1完成確認**
    - 株価チャート（ローソク足 + MA + 出来高）
    - 株価データ・テクニカル指標テーブル
    - 推奨履歴（予測vs実績チャート + 詳細リスト）
    - システム説明バナー
    - 全機能正常動作確認

### 🎯 現在の状態（2026-07-22 夜）

**環境**:
- ✅ DevContainer起動中
- ✅ PostgreSQL 15起動中（localhost:5432）
- ✅ Redis 7起動中（localhost:6379）
- ✅ Backend起動中（http://localhost:8000）
- ✅ Frontend起動中（http://localhost:3000）
- ✅ FE⇄BE API疎通確認済み

**データベース**:
- ✅ 7テーブル作成完了（markets, sectors, stock_master, rounds, round_recommendations, stock_prices_daily, technical_indicators）
- ✅ マスタデータ投入完了（市場6件、業種33件）
- ✅ モックデータ投入完了（銘柄10件、ラウンド2件、推奨10件）
- ✅ **株価+テクニカル指標240日分投入完了**（トヨタ7203）
- ✅ sector/market正規化完了（外部キー設定）
- ✅ 指数フラグ追加完了（is_nikkei225, is_topix等）

**Backend API**:
- ✅ GET /api/v1/rounds（全ラウンド一覧）
- ✅ GET /api/v1/rounds/{round_id}/recommendations（推奨銘柄詳細）
- ✅ **GET /api/v1/stocks/{stock_code}（銘柄基本情報）**
- ✅ **GET /api/v1/stocks/{stock_code}/prices（株価履歴240日分）**
- ✅ **GET /api/v1/stocks/{stock_code}/technical-indicators（主要14指標）**
- ✅ **GET /api/v1/stocks/{stock_code}/technical-indicators/full（全125指標）**
- ✅ **GET /api/v1/stocks/{stock_code}/recommendations（推奨履歴）**
- ✅ sector_name, market_name正常表示

**Frontend**:
- ✅ SSR実装完了
- ✅ OpenAPI型生成完了
- ✅ Tailwind CSS v4設定完了
- ✅ shadcn/uiコンポーネント実装完了
- ✅ VSCode風ダークモードUI完成
- ✅ メインページ完成（BUY/SELL両方表示）
- ✅ Header実装（システム説明バナー + ナビゲーション）
- ✅ RankBadge/RecommendationCard実装
- ✅ 日付表示UX改善（曜日付き + 更新情報）
- ✅ ネオン効果実装完了（グロー、パルスアニメーション）
- ✅ クリック可能なカードUI実装
- ✅ **銘柄詳細ページv1完成** 🎉
  - 株価チャート（ローソク足 + 移動平均線 + 出来高）
  - 株価データ・テクニカル指標テーブル
  - 推奨履歴（予測vs実績チャート + 詳細リスト）
  - タブ切り替えUI
  - TradingView Lightweight Charts v5.2.0使用

**ブランチ**: feature/stock_detail

### 📝 次のタスク

**✅ フェーズ2完了: 銘柄詳細ページv1完成**
- 株価チャート、テクニカル指標、推奨履歴の可視化
- 予測vs実績の比較機能
- タブ切り替えUI

**🎯 フェーズ3: その他ページ追加**
1. 過去のラウンド結果ページ（/history）
   - 過去のラウンド一覧
   - パフォーマンスサマリー
2. Aboutページ（/about）
   - システムの説明
   - 使い方ガイド
3. 404ページ
4. 日経225/TOPIXフィルターページ（/nikkei225, /topix）

**フェーズ4: 実データ連携（現在はモックデータ）**
1. 「先週の実績」セクションを実データに接続
2. round_resultsテーブルとの連携実装
3. パフォーマンス計算ロジック実装
4. 複数銘柄のモックデータ追加（推奨履歴を充実させる）

**フェーズ5: J-Quants API連携 + データ蓄積バッチ**
- J-Quants APIクライアント実装
- データ収集バッチ（日次）
- テクニカル指標計算バッチ
- 週次ラウンド結果検証バッチ

**フェーズ6: 機械学習実装（最終フェーズ）**
- 特徴量エンジニアリング
- モデル学習・評価
- 週次推論パイプライン

---

## 参考情報

### 参考プロジェクト

- **jobsan** (`/Users/hh/dev/github/jobsan`)
  - モノレポ構成の参考
  - DevContainer設定の参考
  - Backend（FastAPI + DDD）の参考
  - Frontend（Next.js + Turborepo）の参考

### 参考記事

- [J-QuantsとAIが切り拓く、個人投資家の新境地](https://note.com/noted_jacana411/n/nf45def4f7fba)
  - システムの発想元
  - 定量分析モデルの参考

---

## 作成済みドキュメント一覧

### ✅ 完成済み（全て）

| ドキュメント | 内容 | 重要度 |
|------------|------|--------|
| **CLAUDE.md** | プロジェクト概要・作業ルール | ⭐⭐⭐ |
| **docs/README.md** | ドキュメント索引 | ⭐⭐⭐ |
| **docs/project-overview.md** | プロジェクト概要詳細版 | ⭐⭐⭐ |
| **docs/directory-structure.md** | モノレポ構成 | ⭐⭐⭐ |
| **docs/database/schemas.md** | 全テーブル定義（24テーブル） | ⭐⭐⭐ |
| **docs/database/guidelines.md** | DB設計ガイドライン | ⭐⭐ |
| **docs/backend/structure.md** | Backend DDD構造 | ⭐⭐⭐ |
| **docs/backend/coding-style.md** | Backend コーディング規約 | ⭐⭐ |
| **docs/frontend/structure.md** | Frontend構造 | ⭐⭐⭐ |
| **docs/frontend/coding-style.md** | Frontend コーディング規約 | ⭐⭐ |
| **docs/frontend/user-guide.md** | 一般ユーザー向け「使い方」ページ | ⭐⭐ |
| **docs/infrastructure/local-development.md** | DevContainer使い方 | ⭐⭐⭐ |

### ⏳ 未作成（実装フェーズで必要になったら作成）

以下は実装を進めながら作成していく:

- docs/architecture/system-architecture.md（システム全体アーキテクチャ図）
- docs/architecture/data-pipeline.md（データパイプライン詳細）
- docs/architecture/ml-workflow.md（ML ワークフロー詳細）
- docs/backend/development-guide.md（開発手順）
- docs/backend/api-specification.md（API仕様詳細）
- docs/frontend/environment.md（環境変数管理）
- docs/ml/data-sources.md（J-Quants API詳細）
- docs/ml/features.md（特徴量設計詳細）
- docs/ml/models.md（モデル設計）
- docs/ml/training-pipeline.md（学習パイプライン）
- docs/batch/*.md（バッチ処理詳細）
- docs/infrastructure/deployment.md（デプロイ手順）
- docs/infrastructure/monitoring.md（監視・ログ設計）

**方針**: 必要になったタイミングで作成することで、実装と乖離しないドキュメントを維持する

---

## 最終更新

- **日時**: 2026-07-22 夜（銘柄詳細ページv1完成 + システム説明バナー追加）
- **作業者**: Claude Code
- **セッション**: feature/stock_detailブランチでの銘柄詳細ページ完全実装
- **進捗**:
  - ✅ **株価チャート実装**（TradingView Lightweight Charts v5.2.0）
    - ローソク足チャート + MA5/MA25/MA75 + 出来高ヒストグラム
    - lightweight-charts v5 API対応（`addSeries()`メソッド使用）
    - ダークモード対応、レスポンシブ対応
  - ✅ **コンポーネント配置整理**
    - `stocks/[stock_code]/_components/` ディレクトリ作成
    - プライベートコンポーネントの整理（将来的な共通化を見据えて）
  - ✅ **推奨履歴タブUI + 折れ線グラフ実装**
    - タブ切り替え：予測vs実績チャート / 詳細リスト
    - 予測騰落率と実績騰落率の推移を折れ線グラフで比較
    - 予測精度が一目でわかる可視化
    - 日付フォーマット：MM/dd形式（例: 07/20）
  - ✅ **UIブラッシュアップ**
    - 全セクションから件数表示を削除（情報過多を解消）
    - タイトルを簡素化（シンプルで見やすいUI）
  - ✅ **Headerにシステム説明バナー追加**
    - 「個人投資家に クオンツ分析 × AI によるデータ・ドリブンな株取引を」
    - 非sticky配置（スクロールで消える）、グラデーション装飾
    - ナビゲーション「About」→「使い方」に変更
  - ✅ **銘柄詳細ページv1完成**
    - 銘柄基本情報、最新株価、株価チャート、テクニカル指標、推奨履歴
    - タブ切り替えUI（株価：チャート/データ/テクニカル指標、推奨履歴：チャート/詳細）
    - 予測vs実績の可視化
- **重要な設計決定**:
  - コンポーネント配置ルール確立（プライベートも `_components/` に配置）
  - 推奨履歴の可視化方針確定（折れ線グラフ + 詳細リスト）
  - lightweight-charts v5 API移行（v4からの破壊的変更に対応）
  - UIの簡素化方針（件数表示削除、タイトル簡略化）
  - システム説明バナーによる価値提案の明示化
- **今回の成果**: 銘柄詳細ページv1完成 🎉
- **次回**: フェーズ3（過去のラウンド結果ページ、使い方ページ等の追加）
