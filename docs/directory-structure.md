# ディレクトリ構造

## プロジェクト全体構成

platinum-axeは、**モノレポ構成**で、以下の4つの主要ディレクトリで構成されます。

```
platinum-axe/
├── frontend/                # フロントエンド（Next.js）
├── backend/                 # バックエンド（FastAPI）
├── ml/                      # 機械学習
├── batch/                   # バッチ処理
├── docs/                    # ドキュメント
├── .devcontainer/           # DevContainer設定（将来追加）
├── CLAUDE.md                # Claude Code作業ルール
└── README.md                # プロジェクト概要
```

---

## Frontend構成

**技術スタック**: Next.js 15 (App Router) + React 19 + TypeScript + TanStack Query + shadcn/ui + Tailwind CSS v4

**特徴**:
- ❌ Turborepo不要（アプリ1つのみ）
- ✅ シンプルなNext.js構成
- ✅ Backend APIから型自動生成（@hey-api/openapi-ts）
- ❌ 認証なし（将来的にFirebase Auth導入予定）

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # ルートレイアウト
│   ├── page.tsx                  # トップページ
│   ├── rounds/                   # ラウンド一覧・詳細
│   │   ├── page.tsx              # ラウンド一覧
│   │   └── [roundId]/
│   │       └── page.tsx          # ラウンド詳細
│   ├── signals/                  # デイリーシグナル
│   │   └── page.tsx
│   └── stocks/                   # 銘柄詳細
│       └── [stockCode]/
│           └── page.tsx
│
├── components/                   # Reactコンポーネント
│   ├── ui/                       # shadcn/uiコンポーネント
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   └── ...
│   ├── rounds/                   # ラウンド関連コンポーネント
│   │   ├── round-card.tsx
│   │   ├── round-list.tsx
│   │   └── recommendation-table.tsx
│   ├── signals/                  # シグナル関連コンポーネント
│   │   └── signal-card.tsx
│   ├── stocks/                   # 銘柄関連コンポーネント
│   │   ├── stock-chart.tsx
│   │   └── stock-info.tsx
│   └── layout/                   # レイアウトコンポーネント
│       ├── header.tsx
│       ├── footer.tsx
│       └── nav.tsx
│
├── lib/                          # ライブラリ・ユーティリティ
│   ├── api/                      # API Client（openapi-ts生成）
│   │   ├── client.ts             # APIクライアント設定
│   │   └── generated/            # 自動生成ファイル
│   │       ├── client.gen.ts
│   │       ├── types.gen.ts
│   │       └── ...
│   ├── hooks/                    # カスタムフック
│   │   ├── use-rounds.ts         # ラウンドデータ取得（TanStack Query）
│   │   ├── use-signals.ts        # シグナルデータ取得
│   │   └── use-stock.ts          # 銘柄データ取得
│   ├── utils/                    # ユーティリティ関数
│   │   ├── format.ts             # フォーマット関数（日付・数値等）
│   │   └── cn.ts                 # classname utility
│   └── types/                    # 追加型定義（必要に応じて）
│       └── index.ts
│
├── public/                       # 静的ファイル
│   ├── favicon.ico
│   └── images/
│
├── styles/                       # グローバルスタイル
│   └── globals.css               # Tailwind CSS
│
├── .eslintrc.json                # ESLint設定
├── next.config.js                # Next.js設定
├── package.json                  # 依存関係
├── postcss.config.js             # PostCSS設定
├── tailwind.config.ts            # Tailwind CSS設定
├── tsconfig.json                 # TypeScript設定
└── openapi-ts.config.ts          # OpenAPI型生成設定
```

### 主要ファイルの役割

| ファイル | 役割 |
|---------|------|
| `app/` | Next.js App Routerのページ・レイアウト |
| `components/ui/` | shadcn/uiの再利用可能UIコンポーネント |
| `components/rounds/` | ラウンド機能のビジネスロジック含むコンポーネント |
| `lib/api/generated/` | Backend APIから自動生成された型定義 |
| `lib/hooks/` | TanStack Queryを使ったデータフェッチhooks |
| `lib/utils/` | 共通ユーティリティ関数 |

---

## Backend構成

**技術スタック**: FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + Redis

**アーキテクチャ**: DDD（Domain-Driven Design）

**参考**: jobsanプロジェクトの構成を踏襲

```
backend/
├── app/
│   ├── main.py                   # FastAPIエントリーポイント
│   ├── config.py                 # 設定管理（環境変数）
│   ├── container.py              # DIコンテナ（dependency-injector）
│   │
│   ├── domain/                   # ドメイン層（ビジネスロジック）
│   │   ├── __init__.py
│   │   ├── models/               # ドメインモデル
│   │   │   ├── __init__.py
│   │   │   ├── stock.py          # 銘柄
│   │   │   ├── round.py          # ラウンド
│   │   │   ├── recommendation.py # 推奨銘柄
│   │   │   └── signal.py         # デイリーシグナル
│   │   ├── repositories/         # リポジトリインターフェース
│   │   │   ├── __init__.py
│   │   │   ├── stock_repository.py
│   │   │   ├── round_repository.py
│   │   │   └── signal_repository.py
│   │   └── services/             # ドメインサービス
│   │       ├── __init__.py
│   │       └── round_service.py
│   │
│   ├── usecase/                  # ユースケース層（アプリケーションロジック）
│   │   ├── __init__.py
│   │   ├── rounds/
│   │   │   ├── __init__.py
│   │   │   ├── get_rounds.py     # ラウンド一覧取得
│   │   │   ├── get_round_detail.py
│   │   │   └── get_round_results.py
│   │   ├── signals/
│   │   │   ├── __init__.py
│   │   │   └── get_daily_signals.py
│   │   └── stocks/
│   │       ├── __init__.py
│   │       ├── get_stock_list.py
│   │       └── get_stock_detail.py
│   │
│   ├── infrastructure/           # インフラ層（外部システム連携）
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py     # DB接続
│   │   │   ├── models.py         # SQLAlchemyモデル（全テーブル）
│   │   │   └── repositories/     # リポジトリ実装
│   │   │       ├── __init__.py
│   │   │       ├── stock_repository_impl.py
│   │   │       ├── round_repository_impl.py
│   │   │       └── signal_repository_impl.py
│   │   ├── cache/
│   │   │   ├── __init__.py
│   │   │   └── redis_client.py   # Redis接続
│   │   └── external/             # 外部API（将来追加）
│   │       ├── __init__.py
│   │       └── jquants_client.py # J-Quants APIクライアント
│   │
│   └── presentation/             # プレゼンテーション層（API）
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dependencies.py   # FastAPI依存性注入
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   ├── router.py     # v1ルーター統合
│       │   │   ├── rounds.py     # ラウンドAPI
│       │   │   ├── signals.py    # シグナルAPI
│       │   │   └── stocks.py     # 銘柄API
│       │   └── health.py         # ヘルスチェック
│       └── schemas/              # Pydanticスキーマ（リクエスト/レスポンス）
│           ├── __init__.py
│           ├── round.py
│           ├── signal.py
│           └── stock.py
│
├── alembic/                      # DBマイグレーション
│   ├── versions/                 # マイグレーションファイル
│   │   └── 001_create_initial_tables.py
│   ├── env.py
│   └── script.py.mako
│
├── tests/                        # テスト
│   ├── __init__.py
│   ├── unit/                     # ユニットテスト
│   │   ├── domain/
│   │   ├── usecase/
│   │   └── infrastructure/
│   └── integration/              # 統合テスト
│       └── api/
│
├── .env.example                  # 環境変数サンプル
├── alembic.ini                   # Alembic設定
├── pyproject.toml                # 依存関係・ツール設定
└── README.md
```

### DDD層の責務

| 層 | 責務 | 依存方向 |
|----|------|---------|
| **Domain** | ビジネスロジック・ドメインモデル | 他に依存しない |
| **UseCase** | アプリケーションロジック・ユースケース | Domain層のみ依存 |
| **Infrastructure** | DB・外部API・キャッシュ等の実装 | Domain層に依存 |
| **Presentation** | API・リクエスト/レスポンス | UseCase層に依存 |

**依存の方向**: `Presentation → UseCase → Domain ← Infrastructure`

---

## ML構成

**技術スタック**: Python 3.12 + LightGBM + pandas + scikit-learn + Jupyter Notebook

```
ml/
├── notebooks/                    # Jupyter Notebook（分析・実験）
│   ├── 01_exploratory_analysis.ipynb    # データ探索
│   ├── 02_feature_engineering.ipynb     # 特徴量設計
│   ├── 03_model_training.ipynb          # モデル学習
│   └── 04_model_evaluation.ipynb        # モデル評価
│
├── features/                     # 特徴量エンジニアリング
│   ├── __init__.py
│   ├── fundamental.py            # ファンダメンタル特徴量
│   ├── technical.py              # テクニカル特徴量
│   ├── sentiment.py              # センチメント特徴量
│   └── feature_store.py          # 特徴量保存・読み込み
│
├── models/                       # モデル学習・保存
│   ├── __init__.py
│   ├── lightgbm_model.py         # LightGBMモデル
│   ├── model_trainer.py          # モデル訓練
│   └── saved_models/             # 保存済みモデル
│       └── round_predictor_v1.pkl
│
├── evaluation/                   # モデル評価
│   ├── __init__.py
│   ├── metrics.py                # 評価指標計算
│   └── backtesting.py            # バックテスト
│
├── prediction/                   # 推論スクリプト
│   ├── __init__.py
│   ├── round_predictor.py        # ラウンド推奨生成
│   └── signal_detector.py        # デイリーシグナル検出
│
├── config/                       # ML設定
│   ├── __init__.py
│   └── model_config.py           # モデルパラメータ設定
│
├── utils/                        # ユーティリティ
│   ├── __init__.py
│   └── data_loader.py            # データ読み込み
│
└── requirements.txt              # 依存関係（ML専用）
```

---

## Batch構成

**技術スタック**: Python 3.12 + asyncio + schedule

```
batch/
├── data_collection/              # データ収集バッチ
│   ├── __init__.py
│   ├── collect_stock_prices.py   # 株価データ取得
│   ├── collect_financials.py     # 財務データ取得
│   ├── collect_margin_trading.py # 信用取引データ取得
│   └── collect_market_data.py    # 市場データ取得
│
├── preprocessing/                # 前処理バッチ
│   ├── __init__.py
│   ├── calculate_technical_indicators.py  # テクニカル指標計算
│   └── generate_ml_features.py   # ML特徴量生成
│
├── prediction/                   # 予測バッチ
│   ├── __init__.py
│   ├── weekly_round_prediction.py    # 週次ラウンド推奨生成
│   ├── daily_signal_detection.py     # デイリーシグナル検出
│   └── result_verification.py        # 結果検証
│
├── model_training/               # モデル再学習バッチ
│   ├── __init__.py
│   └── retrain_model.py
│
├── common/                       # 共通処理
│   ├── __init__.py
│   ├── db_connector.py           # DB接続
│   ├── jquants_client.py         # J-Quants APIクライアント
│   └── logger.py                 # ログ設定
│
├── scheduler/                    # バッチスケジューラ
│   ├── __init__.py
│   └── batch_scheduler.py        # バッチ実行スケジュール管理
│
└── requirements.txt              # 依存関係（バッチ専用）
```

### バッチ実行スケジュール

| バッチ | 実行タイミング | 処理内容 |
|-------|-------------|---------|
| **株価データ収集** | 毎営業日 17:30 | J-Quants APIから株価取得 |
| **テクニカル指標計算** | 毎営業日 18:00 | 移動平均、RSI等を計算 |
| **デイリーシグナル検出** | 毎営業日 18:30 | 強い売買シグナル検出 |
| **週次ラウンド推奨** | 週末（土曜朝） | 来週の推奨銘柄生成 |
| **結果検証** | 週末（土曜朝） | 先週ラウンドの結果検証 |
| **モデル再学習** | 月次 | 最新データでモデル再訓練 |

---

## 共通設定・ドキュメント

```
platinum-axe/
├── .devcontainer/                # DevContainer設定（将来追加）
│   ├── devcontainer.json
│   ├── docker-compose.yml
│   └── Dockerfile
│
├── docs/                         # ドキュメント（このファイル含む）
│   ├── README.md
│   ├── directory-structure.md    # このファイル
│   ├── project-overview.md
│   ├── architecture/
│   ├── backend/
│   ├── frontend/
│   ├── ml/
│   ├── batch/
│   ├── database/
│   └── infrastructure/
│
├── .gitignore
├── CLAUDE.md                     # Claude Code作業ルール
└── README.md                     # プロジェクト概要
```

---

## 開発フロー

### 1. Frontend開発

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:3000
```

### 2. Backend開発

```bash
cd backend
uv sync --all-extras
uvicorn app.main:app --reload --port 8000
```

### 3. マイグレーション

```bash
cd backend
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

### 4. ML実験

```bash
cd ml
jupyter notebook  # notebooksディレクトリで実験
```

### 5. バッチ実行

```bash
cd batch
python data_collection/collect_stock_prices.py
```

---

## ファイル命名規則

### Backend（Python）
- **ファイル名**: `snake_case.py`
- **クラス名**: `PascalCase`
- **関数名**: `snake_case`
- **定数**: `UPPER_SNAKE_CASE`

### Frontend（TypeScript）
- **ファイル名**: `kebab-case.tsx` or `kebab-case.ts`
- **コンポーネント**: `PascalCase`
- **関数名**: `camelCase`
- **定数**: `UPPER_SNAKE_CASE`

### データベース
- **テーブル名**: `snake_case`（複数形）
- **カラム名**: `snake_case`

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
