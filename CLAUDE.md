# Claude Code 作業ルール - プラチナの斧（platinum-axe）

## 概要

**プロジェクト名**: プラチナの斧（platinum-axe）

J-Quants APIを活用した機械学習による**日本株銘柄推奨システム**。

**目的**: 個人投資家向けの投資判断支援ツール

**特徴**:
- ✅ 週次ラウンド制（買い推奨 / 売り推奨 各Top10）
- ✅ LightGBM（勾配ブースティング）による予測
- ✅ J-Quants API Standardプラン（10年データ）
- ✅ トランザクションデータ保存 + テクニカル指標事前計算（125項目）

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

### 2. 機械学習モデル

- **アルゴリズム**: LightGBM（勾配ブースティング）
- **予測ターゲット**: 翌週の騰落率（回帰）
- **特徴量**: ファンダメンタル + テクニカル125項目 + 市場センチメント + マクロ経済

---

## 技術スタック

**参考プロジェクト**: jobsan (`/Users/hh/dev/github/jobsan`)

### Backend
- **Python 3.12** + **uv**
- **FastAPI** + **SQLAlchemy 2.0** + **Alembic**
- **PostgreSQL 15** + **Redis**
- **DDD構造** (domain/usecase/infrastructure/presentation)

### Frontend
- **Node.js 22** + **pnpm**
- **Next.js 15** (App Router) + **React 19** + **TypeScript**
- **@hey-api/openapi-ts** (Backend API型自動生成)
- **shadcn/ui** + **Tailwind CSS v4**
- **TradingView Lightweight Charts v5**

### 機械学習
- **Python 3.12** + **LightGBM** + **pandas, numpy, scikit-learn**

### インフラ
- **VSCode DevContainer** + **Docker Compose**
- **GCP** (将来的なデプロイ先)

---

## Claude Code 作業ルール

### 1. セッション開始時の必須確認事項

1. **このCLAUDE.mdを読む** - 現在の作業状況を確認
2. **「現在の状態」セクションを確認** - FE/BE/DBの状態を把握
3. **「次のタスク」を確認** - 何をすべきか明確にする
4. **docs/を参照する** - 実装方針・アーキテクチャを確認

### 2. ファイル変更時の原則

**必ず開発者と合意してからファイル変更を行うこと**

### 3. CLAUDE.md の継続的な更新（重要）

作業が一区切りついたら、**必ず CLAUDE.md の「現在の状態」を更新する**

### 4. docs/の内容に準拠すること（最重要）

実装時は必ずdocs/の内容に従うこと。推測で実装しない。

### 5. 禁止事項（許可なく実行しないこと）

**開発者の明示的な許可がない限り実行禁止**：

- ❌ Database操作（`alembic upgrade/downgrade`, シードデータ投入）
- ❌ Git操作（`git commit/push/merge/rebase`）
- ❌ 環境・設定ファイル変更（`.env`, `pyproject.toml`, `package.json`, DevContainer設定）
- ❌ 破壊的操作（ファイル削除、ディレクトリ構造の大幅変更、本番環境操作）

---

## 現在の状態（2026-07-24 深夜）

### 環境

- ✅ DevContainer起動中
- ✅ PostgreSQL 15起動中（localhost:5432）
- ✅ Redis 7起動中（localhost:6379）
- ✅ Backend起動中（http://localhost:8000）
- ✅ Frontend起動中（http://localhost:3000）
- ✅ FE⇄BE API疎通確認済み

### コード品質ツール

- ✅ **Frontend**: Biome 2.5.5導入済み（46ファイルフォーマット完了）
- ✅ **Backend**: Ruff 0.15.22動作確認済み（22ファイルフォーマット完了）
- ✅ README.md更新（Linter/Formatterコマンド、Container上実行方法記載）

### データベース

- ✅ 8テーブル作成完了
  - `markets` (市場区分マスタ6件)
  - `sectors` (33業種マスタ33件)
  - `sector17s` (17業種マスタ18件) ✨NEW
  - `stock_master` (銘柄マスタ10件 → 拡張完了: info_date, sector17_code, scale_category, margin_code) ✨UPDATE
  - `rounds` (ラウンド32件)
  - `round_recommendations` (推奨銘柄320件)
  - `stock_prices_daily` (株価240日分 - トヨタのみ)
  - `technical_indicators` (テクニカル指標240日分 - トヨタのみ、125項目)
  - `round_results` (結果データ300件)

### Backend API（13エンドポイント）

**ラウンド管理**:
- `GET /api/v1/rounds` - 全ラウンド一覧
- `GET /api/v1/rounds/{round_id}/recommendations` - 推奨銘柄詳細

**銘柄検索・詳細**:
- `GET /api/v1/stocks/search` - 銘柄検索（銘柄コード・会社名の部分一致）
- `GET /api/v1/stocks/{stock_code}` - 銘柄基本情報
- `GET /api/v1/stocks/{stock_code}/prices` - 株価履歴240日分
- `GET /api/v1/stocks/{stock_code}/technical-indicators` - 主要14指標
- `GET /api/v1/stocks/{stock_code}/technical-indicators/full` - 全125指標
- `GET /api/v1/stocks/{stock_code}/recommendations` - 推奨履歴

**履歴管理**:
- `GET /api/v1/history/latest` - 直近結果（メインページ用）
- `GET /api/v1/history` - 履歴一覧（ページネーション）
- `GET /api/v1/history/summary` - 全体統計
- `GET /api/v1/history/{round_id}` - ラウンド詳細

**ヘルスチェック**:
- `GET /api/v1/health` - API疎通確認

### Frontend（全ページ実装完了）

**実装済みページ**:
- ✅ メインページ（`/all`, `/nikkei225`, `/topix`）- 今週の推奨銘柄
- ✅ 銘柄詳細ページ（`/stocks/[stock_code]`）- チャート + テクニカル指標 + 推奨履歴
- ✅ 過去の結果ページ（`/history`）- 履歴一覧 + パフォーマンスサマリー
- ✅ ラウンド詳細ページ（`/history/[round_id]`）- 推奨 + 結果
- ✅ 使い方ページ（`/about`）- システム説明 + 125項目の特徴量詳細
- ✅ 404ページ（`/not-found`）

**UI/UX特徴**:
- VSCode風ダークモードデザイン
- shadcn/ui コンポーネント
- TradingView Lightweight Charts（ローソク足 + 移動平均線 + 出来高）
- ネオン効果（グロー、パルスアニメーション）
- レスポンシブ対応（PC/SP）
- 銘柄検索機能（オートコンプリート、Debounce処理、PC: Header / SP: ページ本文）

### ディレクトリ構成

**✅ フェーズ5完了: ローカル専用スクリプトと本番バッチジョブを明確に分離**

```
backend/
├── scripts/
│   ├── check_column_names.py       # DB確認ツール
│   └── seeds/                      # ローカル専用シードデータ
│       ├── seed_mock_data.py
│       ├── seed_sectors.py
│       ├── seed_markets.py
│       ├── seed_stock_prices.py
│       ├── seed_round_history.py
│       └── temp/                   # 一時的なスクリプト
│           ├── clean_alembic.py
│           └── reset_db.py
│
└── jobs/                           # GCP Cloud Run Jobsで実行
    ├── collectors/                 # データ収集（J-Quants API）
    │   ├── jquants_client.py       # J-Quants API V2クライアント ✨NEW
    │   └── fetch_stock_master.py   # 銘柄マスタ取得スクリプト ✨NEW
    ├── preprocessors/              # 前処理・指標計算
    │   └── .gitkeep
    └── predictors/                 # 推論
        └── .gitkeep

ml/                                 # 機械学習開発
├── notebooks/                      # Jupyter Notebook（探索的分析）
├── training/                       # モデル学習パイプライン
└── models/                         # 学習済みモデル保存先
    └── .gitkeep
```

### ブランチ

- `main` - メインブランチ
- `feature/jpx_api` - J-Quants API連携実装中（現在のブランチ）

---

## 次のタスク

**✅ フェーズ2完了: 銘柄詳細ページv1完成**
**✅ フェーズ3完了: 過去のラウンド結果ページv1完成**
**✅ フェーズ4完了: 残りのページ追加完了** 🎉
**✅ Linter/Formatter導入完了（Biome + Ruff）**
**✅ フェーズ5完了: ディレクトリ構成リファクタリング完了**
**✅ フェーズ6-1完了: J-Quants API仕様調査 + ドキュメント化完了** 🎉
**✅ フェーズ6-2完了: 銘柄マスタ取得機能実装完了** 🎉

### 🎯 フェーズ6: J-Quants API連携 + データ蓄積バッチ（進行中）

#### ✅ 6-1. J-Quants API仕様調査（完了）

**成果物**:
- ✅ `docs/batch/jquants-api.md` 作成完了
  - Standardプラン全17種のAPI詳細
  - APIとDBテーブルの対応表
  - レート制限、認証方法、バッチ処理設計
- ✅ `docs/database/overview.md` 作成完了
  - Layer構造の説明
  - APIとDBテーブルの対応表（更新頻度・更新時刻・更新ジョブ列付き）
  - 実装状況の可視化
- ✅ `docs/database/schemas/` 作成完了（8テーブル個別ドキュメント化）
  - markets.md, sectors.md, stock_master.md
  - stock_prices_daily.md, technical_indicators.md
  - rounds.md, round_recommendations.md, round_results.md
  - 各テーブルにソースコードへのリンク追加

**アカウント登録**: 開発者が実施（Standardプラン：¥3,300/月）

---

#### ✅ 6-2. 銘柄マスタ取得（完了）

**成果物**:
- ✅ **DBスキーマ拡張**
  - `sector17s` テーブル作成 + マスタデータ18件INSERT
  - `stock_master` テーブル拡張（4カラム追加）
    - `info_date` - 情報適用年月日（更新判断用）
    - `sector17_code` - 17業種コード（外部キー）
    - `scale_category` - 規模区分（TOPIX分類）
    - `margin_code` - 信用区分コード（1: 信用 / 2: 貸借 / 3: その他）
  - Alembicマイグレーション実行完了

- ✅ **ドキュメント**
  - `docs/database/schemas/sector17s.md` 作成
  - `docs/database/schemas/stock_master.md` 更新（コード値説明追加）

- ✅ **実装**
  - `backend/app/domain/models/sector17.py` - Sector17モデル作成
  - `backend/app/domain/models/stock.py` - StockMasterモデル拡張
  - `backend/jobs/collectors/jquants_client.py` - J-Quants API V2クライアント
  - `backend/jobs/collectors/fetch_stock_master.py` - 銘柄マスタ取得スクリプト
  - `backend/.env.example` 更新（JQUANTS_API_KEY追加）

**動作確認**:
- ✅ API接続テスト成功（全4444銘柄取得確認）
- ⏸️ 銘柄マスタ取得スクリプト実行（次回セッションで実行予定）

---

#### 6-3. 株価データ取得（銘柄マスタ取得後）

**目的**: 過去10年分（2015〜2025）の全銘柄株価データを取得

**実装予定**: 銘柄マスタ取得完了後に着手
2. 各銘柄ループ
   - 株価データ取得（10年分）
   - DB保存（`stock_prices_daily`）
   - 進捗保存（JSON）
   - レート制限対策（sleep）
3. 完了通知

---

#### 6-4. 日次差分データ取得

**ファイル**: `backend/jobs/collectors/collect_daily_data.py`

**目的**: 毎営業日の最新データを取得

**仕様**:
- **実行タイミング**: 毎営業日17:30（Cloud Schedulerで自動実行）
- **対象期間**: 前営業日1日分
- **対象銘柄**: 全銘柄（約3000銘柄）
- **所要時間**: 5〜10分
- **エラー対策**: リトライ + Slack通知

**コマンド例**:
```bash
# ローカルテスト時
uv run python backend/jobs/collectors/collect_daily_data.py \
  --date 2025-12-23  # 省略時は前営業日
```

**処理フロー**:
1. 対象日付決定（前営業日）
2. 銘柄一覧取得
3. 各銘柄の株価取得
4. DB保存（`stock_prices_daily`）
5. テクニカル指標計算トリガー
6. 完了通知

---

#### 6-5. テクニカル指標計算バッチ

**ファイル**: `backend/jobs/preprocessors/calculate_technical_indicators.py`

**目的**: 株価データから125種類のテクニカル指標を計算

**実行タイミング**:
- 初回: 全期間・全銘柄を一括計算
- 日次: 前営業日分のみ追加計算

---

#### 6-6. GCPデプロイ

**タイミング**: ローカルで動作確認後

**サービス構成**:
```
Cloud Scheduler
  └─> Cloud Run Jobs (collect_daily_data)
        └─> Cloud SQL (PostgreSQL)
```

**デプロイ手順**:
1. Dockerfile作成（DevContainer用を流用）
2. Container Registry登録
3. Cloud Run Jobs作成
4. Cloud Scheduler設定（cron: 0 17 * * 1-5）
5. 環境変数設定（J-Quants API Key等）

---

### フェーズ7: 機械学習実装（最終フェーズ）

#### 7-1. ローカルでモデル構築

**場所**: `ml/notebooks/`

**開発方針**:
- ✅ **最初はローカル（Jupyter Notebook）で試行錯誤**
- ✅ LightGBMは軽量なのでローカルで十分（GPU不要）
- ✅ 全銘柄×10年データでも数分〜数十分で学習完了
- ❌ GCPは不要（週次再学習の自動化時のみ使用）

**実装ステップ**:
1. **データ探索**（`01_data_exploration.ipynb`）
   - トヨタ1銘柄で分析
   - 株価・テクニカル指標の可視化
   - 欠損値確認

2. **特徴量エンジニアリング**（`02_feature_engineering.ipynb`）
   - 125項目の特徴量設計
   - 相関分析
   - 特徴量重要度確認

3. **モデル学習・評価**（`03_model_training.ipynb`）
   - LightGBMで翌週騰落率予測（回帰）
   - 訓練/検証/テストデータ分割
   - ハイパーパラメータ調整
   - 予測精度評価（RMSE, MAE, R²）

4. **Pythonスクリプト化**
   - `ml/training/train_model.py` 作成
   - コマンドラインから実行可能に

---

#### 7-2. 週次推論パイプライン

**ファイル**: `backend/jobs/predictors/generate_weekly_predictions.py`

**目的**: 週末に翌週の推奨銘柄（買い/売り Top10）を算出

**実行タイミング**: 毎週土曜朝（Cloud Schedulerで自動実行）

**処理フロー**:
1. 全銘柄の最新特徴量取得
2. 学習済みモデルで翌週騰落率予測
3. 予測値上位/下位Top10抽出
4. `rounds`, `round_recommendations`に保存
5. 月曜朝のWebサイト表示に反映

---

### 実装優先順位まとめ

**重要**: Jupyter Notebookでモデル検証するには**実データが必須**なので、データ取得を最優先する。

```
✅ 完了:
  1. フェーズ5: ディレクトリリファクタリング完了
  2. フェーズ6-1: J-Quants API仕様調査 + ドキュメント化完了

次のセッション（APIキー受領後）:
  3. フェーズ6-2: 銘柄マスタ取得（最優先！）
     - APIクライアント実装
     - 銘柄マスタ取得スクリプト実装
     - 全銘柄約3800件のデータ取得

その後:
  4. フェーズ6-3: 株価データ取得（過去10年分）
     - 初回全件データ取得（2015〜2025）
     - 少なくとも数銘柄×1年分のデータがあればJupyter Notebook開始可能
  5. フェーズ7-1: Jupyter Notebookでモデル構築（データ探索から開始）
  6. フェーズ6-4: 日次差分取得実装
  7. フェーズ6-5: テクニカル指標計算バッチ
  8. フェーズ7-2: 週次推論パイプライン
  9. フェーズ6-6: GCPデプロイ（自動化）
```

**段階的アプローチ**:
- まず銘柄マスタ取得で全銘柄情報を確保
- 株価データは1〜2銘柄の過去1年分で動作確認
- Jupyter Notebookでプロトタイプ検証可能になったら並行作業
- バックグラウンドで全銘柄×10年データ取得継続

---

## ドキュメント構成

詳細な仕様・設計は`docs/`配下に集約されています：

### ✅ 完成済み

| ドキュメント | 内容 | 重要度 |
|------------|------|--------|
| **CLAUDE.md** | プロジェクト概要・作業ルール | ⭐⭐⭐ |
| **CLAUDE_HISTORY.md** | 完了した作業の詳細履歴 | ⭐⭐ |
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

- docs/architecture/system-architecture.md
- docs/backend/api-specification.md
- docs/ml/*.md（特徴量設計、モデル設計、学習パイプライン）
- docs/batch/*.md（バッチ処理詳細）
- docs/infrastructure/deployment.md

---

## 参考情報

### 参考プロジェクト

- **jobsan** (`/Users/hh/dev/github/jobsan`) - モノレポ構成、DevContainer設定、Backend（FastAPI + DDD）、Frontend（Next.js）の参考

### 参考記事

- [J-QuantsとAIが切り拓く、個人投資家の新境地](https://note.com/noted_jacana411/n/nf45def4f7fba) - システムの発想元

---

## 最終更新

- **日時**: 2026-07-24 深夜（フェーズ6-2：銘柄マスタ取得機能実装完了）
- **作業者**: Claude Code
- **ブランチ**: feature/jpx_api
- **変更内容**:
  - ✅ **フェーズ6-2完了: 銘柄マスタ取得機能実装**
    - **DBスキーマ拡張**
      - Alembicマイグレーション作成・実行完了
      - `sector17s` テーブル作成 + マスタデータ18件INSERT
      - `stock_master` テーブル拡張（4カラム追加: info_date, sector17_code, scale_category, margin_code）
    - **ドキュメント**
      - `docs/database/schemas/sector17s.md` 作成
      - `docs/database/schemas/stock_master.md` 更新（コード値説明追加）
    - **モデル実装**
      - `backend/app/domain/models/sector17.py` 作成
      - `backend/app/domain/models/stock.py` 拡張
      - `backend/app/domain/models/__init__.py` 更新
    - **APIクライアント・スクリプト実装**
      - `backend/jobs/collectors/jquants_client.py` 実装
      - `backend/jobs/collectors/fetch_stock_master.py` 実装
      - `backend/.env.example` 更新
    - **動作確認**
      - API接続テスト成功（全4444銘柄取得確認）
      - 規模区分6種類、信用区分3種類を確認
- **次回**: フェーズ6-2の続き
  - 銘柄マスタ取得スクリプト実行（約4400銘柄のDB保存）
  - スクリプトの改善（DATABASE_URL環境変数化、指数組入判定ロジック実装）
  - 動作確認・デバッグ
