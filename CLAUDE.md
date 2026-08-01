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
- **特徴量（Phase 1 MVP）**: テクニカル125項目 + ファンダメンタル20項目 + セクター指数19項目 + 信用倍率5項目 = 169項目
- **特徴量（Phase 2 精度向上）**: +マクロ経済10項目（為替、米国株指数、商品） + センチメント指標 = 約200項目

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

### 6. J-Quants API利用規約の遵守（絶対的ルール）

**⚠️ 最重要：違反すると法的問題が発生します**

参考: https://jpx-jquants.com/ja/help/usage

#### ❌ 絶対に禁止（生データの二次配布）

以下のデータを**Webサービス・APIで表示・配布することは禁止**：

1. **株価データ（生データ）**
   - 四本値（始値、高値、安値、終値）
   - 出来高、売買代金
   - 時系列の株価推移

2. **財務データ（生データ）**
   - 決算短信の財務諸表（売上高、純利益等の生の値）
   - EPS、BPS、発行済株式数等の生の値
   - 配当金額（生の値）

3. **その他の生データ**
   - 信用残高（生の値）
   - 空売り比率（生の値）
   - 指数の四本値

#### ✅ 表示可能（独自計算データ）

以下は**独自計算による派生データ**のため表示OK：

1. **テクニカル指標**（125項目）
   - 移動平均、RSI、MACD、ボリンジャーバンド等
   - すべて当サービスの独自計算

2. **ファンダメンタル指標**（20項目）
   - PER、PBR、ROE、ROA、成長率等
   - すべて当サービスの独自計算

3. **機械学習の予測結果**
   - 買い推奨Top10、売り推奨Top10
   - 予測騰落率（%）
   - 予測精度

4. **比率・成長率**
   - 前日比（%）
   - 前年同期比（%）
   - 配当利回り（%）

#### 🔄 代替手段（TradingView Widget使用）

株価・チャート表示には**TradingView Widget**を使用すること：

```tsx
// ✅ OK: TradingView Widget（外部サービス）
<TradingViewWidget symbol="TSE:7203" />

// ❌ NG: J-Quants APIの株価を直接表示
<p>株価: {price}円</p>
```

#### 📝 実装時のチェックリスト

**新しいページ・APIを作成する際、必ず確認**：

- [ ] J-Quants APIの生データを直接表示していないか
- [ ] 株価チャートはTradingView Widgetを使っているか
- [ ] 表示しているのは独自計算の指標のみか
- [ ] APIレスポンスに株価の生データが含まれていないか

**参考ドキュメント**:
- `docs/legal/terms-of-service-draft.md` - 利用規約（第3条）
- `docs/user/calculation-methodology.md` - 計算方法の説明

---

## 現在の状態（2026-07-31 - フェーズ6-7完了：ファンダメンタル指標計算完了）

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

- ✅ 10テーブル作成完了
  - `markets` (市場区分マスタ **10件** - JPX公式コード、Alembic管理)
  - `sectors` (33業種マスタ **34件** - 33業種+9999、Alembic管理)
  - `sector17s` (17業種マスタ18件 - Alembic管理)
  - `stock_master` (銘柄マスタ **4444件** - 全銘柄取得完了)
  - `rounds` (ラウンド32件)
  - `round_recommendations` (推奨銘柄320件)
  - `stock_prices_daily` (株価 **約1100万件** - 全4444銘柄×10年分)
  - `technical_indicators` (テクニカル指標 **約1100万件** - 125項目、全銘柄×10年分完了)
  - `financial_statements` (財務データ **189,882件** - 全銘柄×10年分完了)
  - `fundamental_indicators` (ファンダメンタル指標 **約900万件** - 20項目、全銘柄×10年分完了) ✨NEW
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
    │   ├── fetch_stock_master.py              # 銘柄マスタ取得（初回のみ）
    │   ├── fetch_stock_prices.py              # 株価全量取得（初回のみ）
    │   ├── fetch_daily_stock_prices.py        # 株価差分取得（日次）
    │   ├── fetch_financial_statements.py      # 財務全量取得（初回のみ） ✨NEW
    │   └── fetch_daily_financial_statements.py # 財務差分取得（日次） ✨NEW
    ├── preprocessors/              # 前処理・指標計算
    │   ├── calculate_technical_indicators.py   # テクニカル指標全量計算
    │   └── calculate_daily_technical_indicators.py # テクニカル指標差分計算
    ├── workflows/                  # ワークフロー統合 ✨NEW
    │   └── daily_data_update.py   # 日次データ更新（株価→財務→テクニカル） ✨NEW
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
- `feature/jpx_api_v2` - J-Quants API連携実装中（現在のブランチ）

---

## 次のタスク

**✅ フェーズ2完了: 銘柄詳細ページv1完成**
**✅ フェーズ3完了: 過去のラウンド結果ページv1完成**
**✅ フェーズ4完了: 残りのページ追加完了** 🎉
**✅ Linter/Formatter導入完了（Biome + Ruff）**
**✅ フェーズ5完了: ディレクトリ構成リファクタリング完了**
**✅ フェーズ6-1完了: J-Quants API仕様調査 + ドキュメント化完了** 🎉
**✅ フェーズ6-2完了: 銘柄マスタ取得機能実装完了** 🎉
**✅ フェーズ6-3完了: 株価データ取得機能実装完了** 🎉
**✅ フェーズ6-4完了: 日次差分取得実装完了（DDD構造リファクタリング）** 🎉
**✅ フェーズ6-5完了: テクニカル指標計算バッチ完了（125項目、約1100万件）** 🎉
**✅ フェーズ6-6完了: 財務データ取得完了（189,882件、10年分）** 🎉
**✅ Phase 1特徴量構成確定: 169項目（信用倍率追加）** 🎉
**✅ 日次データ更新ワークフロー完成: 株価→財務→テクニカル** 🎉

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
  - `sector17s` テーブル作成 + マスタデータ18件INSERT（Alembic管理）
  - `markets` テーブル置き換え（JPX公式コード10件、Alembic管理）
  - `sectors` テーブル置き換え（東証公式34件、Alembic管理）
  - `stock_master` テーブル拡張（4カラム追加）
    - `info_date` - 情報適用年月日（更新判断用）
    - `sector17_code` - 17業種コード（外部キー）
    - `scale_category` - 規模区分（TOPIX分類）
    - `margin_code` - 信用区分コード（1: 信用 / 2: 貸借 / 3: その他）
  - Alembicマイグレーション3本実行完了
    - `20260724_0100`: sector17s追加
    - `20260724_0200`: markets JPX公式コード化
    - `20260724_0210`: sectors 34件化

- ✅ **ドキュメント**
  - `docs/database/schemas/sector17s.md` 作成
  - `docs/database/schemas/markets.md` 更新（JPX公式コード詳細）
  - `docs/database/schemas/stock_master.md` 更新（コード値説明追加）

- ✅ **実装**
  - `backend/app/domain/models/sector17.py` - Sector17モデル作成
  - `backend/app/domain/models/stock.py` - StockMasterモデル拡張
  - `backend/app/shared/config.py` - J-Quants API V1→V2仕様変更
  - `backend/jobs/collectors/jquants_client.py` - J-Quants API V2クライアント
  - `backend/jobs/collectors/fetch_stock_master.py` - 銘柄マスタ取得スクリプト
  - `backend/.env.example` 更新（JQUANTS_API_KEY追加）
  - `backend/scripts/seeds/seed_markets.py`, `seed_sectors.py` 更新（参考用）

**動作確認**:
- ✅ API接続テスト成功（全4444銘柄取得確認）
- ✅ **銘柄マスタ取得スクリプト実行成功（4444銘柄DB保存完了）** 🎉
- ✅ 外部キー制約クリア（markets, sectors, sector17s）
- ✅ info_dateによる更新判定機能確認

---

#### ✅ 6-3. 株価データ取得（完了）

**目的**: 株価データ取得機能の実装と動作確認

**成果物**:
- ✅ **スクリプト実装**
  - `backend/jobs/collectors/fetch_stock_prices.py` 実装完了
  - 週単位分割（7日ずつ）でrate limit対策
  - 進捗保存機能（JSON）でエラー時の再開対応
  - `--test` オプションで1週間のテスト実行
  - `--resume` オプションで進捗から再開
  - `--wait` オプションで待機時間調整可能

- ✅ **DB拡張**
  - Alembicマイグレーション作成・実行
    - `20260724_2200_d7e8f9g0h1i2`: UNIQUE制約追加
    - `20260724_2300_e8f9g0h1i2j3`: volume列をBIGINTに変更
  - `stock_prices_daily` テーブルにUNIQUE制約追加
  - volume/adjusted_volume列をBIGINT化（21億超の出来高対応）

- ✅ **実装詳細**
  - PostgreSQL UPSERT（`ON CONFLICT DO UPDATE`）で高速保存
  - NaN処理完全対応（pandas → PostgreSQL）
  - 型変換完全対応（Decimal, int, bool）
  - bool変換対応（J-Quants APIの文字列 '0'/'1' → bool）
  - TimestampMixin対応（id, created_at, updated_atを除外）

**動作確認**:
- ✅ テスト実行成功：19,119件を9.08秒でUPSERT完了
- ✅ API取得: 3.12秒（7日分）
- ✅ 全カラム正常保存確認
  - 四本値（open, high, low, close）
  - 出来高（volume, adjusted_volume）
  - ストップ高・安（is_upper_limit, is_lower_limit）
- ✅ ストップ高・安の正しい判定確認
  - 通常: 19,036件（false, false）
  - ストップ安: 27件（false, true）
  - ストップ高: 55件（true, false）
  - 両方該当: 1件（true, true）

**使用例**:
```bash
# テストモード（1週間のみ取得）
uv run python backend/jobs/collectors/fetch_stock_prices.py --test

# 過去10年分取得
uv run python backend/jobs/collectors/fetch_stock_prices.py

# 期間指定
uv run python backend/jobs/collectors/fetch_stock_prices.py --start-date 2024-01-01 --end-date 2024-12-31

# 進捗から再開
uv run python backend/jobs/collectors/fetch_stock_prices.py --resume
```

---

#### ✅ 6-4. 日次差分取得（完了）

**目的**: 毎営業日の最新株価データを自動取得（データ更新の自動化）

**成果物**:
- ✅ **DDD構造リファクタリング完了**
  - Infrastructure層: `JQuantsStockPriceRepository`, `StockPriceDailyRepository`
  - UseCase層: `FetchStockPricesUseCase`
  - Jobs層: `fetch_stock_prices.py`（書き換え）、`fetch_daily_stock_prices.py`（新規）

- ✅ **実装ファイル**
  - `backend/app/infrastructure/jquants/stock_price_repository.py` - J-Quants API呼び出し
  - `backend/app/infrastructure/persistence/stock_price_daily_repository.py` - DB保存（UPSERT）
  - `backend/app/usecase/fetch_stock_prices_usecase.py` - 全件取得・差分取得の調整
  - `backend/jobs/collectors/fetch_stock_prices.py` - 全件取得（500行→165行に削減）
  - `backend/jobs/collectors/fetch_daily_stock_prices.py` - 差分取得（新規）

- ✅ **共通化されたロジック**
  - J-Quants API呼び出し → `JQuantsStockPriceRepository`
  - PostgreSQL UPSERT → `StockPriceDailyRepository`
  - 週単位分割・rate limit対策 → `FetchStockPricesUseCase`
  - NaN/型変換/bool変換 → `StockPriceDailyRepository`

**実装の特徴**:
- ✅ **DRY原則**: 共通ロジックをUseCase/Infrastructureに集約
- ✅ **冪等性**: DBの最新日付ベースで何度実行しても同じ結果
- ✅ **保守性**: API変更時はRepository層のみ修正
- ✅ **柔軟性**: バックフィル（バッチ停止期間の補完）も自動対応
- ✅ **テスタビリティ**: UseCase単体でテスト可能
- ✅ **pod再配置対策**: progress.json不要（DB状態ベース）

**動作確認**:
- ✅ 全件取得テスト: 19,115件（20.4秒）
- ✅ 差分取得テスト（初回）: 8,886件（11.9秒）
- ✅ 差分取得テスト（冪等性）: 差分なし（完全）
- ✅ Ruffエラー解消: All checks passed!

**使用例**:
```bash
# 全件取得（テストモード: 1週間のみ）
uv run python backend/jobs/collectors/fetch_stock_prices.py --test

# 全件取得（過去10年分、wait=2秒で約2時間）
uv run python backend/jobs/collectors/fetch_stock_prices.py --wait 2

# 差分取得（DBの最新日付から自動取得）
uv run python backend/jobs/collectors/fetch_daily_stock_prices.py
```

**実行タイミング**:
- 手動実行: `uv run python backend/jobs/collectors/fetch_daily_stock_prices.py`
- 自動実行: GCP Cloud Scheduler（毎営業日17:30）

**所要時間**:
- 通常（1日分）: 約5-10分
- バックフィル（複数日）: 日数に応じて増加（週単位分割で自動対応）

---

#### 6-5. テクニカル指標計算バッチ

**ファイル**: `backend/jobs/preprocessors/calculate_technical_indicators.py`

**目的**: 株価データから125種類のテクニカル指標を計算

**実装内容**:
- 移動平均（5日、25日、75日、200日）
- RSI、MACD、ボリンジャーバンド
- 出来高指標（OBV、MFI等）
- モメンタム指標（ROC、Stochastic等）
- ボラティリティ指標（ATR等）

**実行タイミング**:
- 初回: 全期間・全銘柄を一括計算（約1100万レコード）
- 日次: 前営業日分のみ追加計算

**データ量**:
- 全4444銘柄 × 約2500営業日 × 125項目 = 約13億データポイント

---

#### ✅ 6-6. ファンダメンタルデータ取得（完了）

**目的**: Phase 1のファンダメンタル指標（20項目）計算のためのデータ取得

**成果物**:
- ✅ **DBテーブル作成**: `financial_statements`（Alembic管理）
  - **主キー**: `id` (UUID, auto-generated)
  - **自然キー（UNIQUE制約）**: `(stock_code, disc_date, type_of_document, disc_time)`
    - `disc_time`はNOT NULL（実データ全件で値が存在、NULL: 0件確認済み）
  - カラム: 売上高、利益、EPS、BPS、CF、配当等（約110カラム）
  - 冪等性: UPSERT（ON CONFLICT DO UPDATE）で自然キー重複を更新
  - Alembicマイグレーション2本実行完了
    - `20260729_2051`: テーブル作成（全カラム定義）
    - `20260729_2125`: UNIQUE制約修正（disc_time追加 + NOT NULL化） + BIGINT化

- ✅ **DDD構造でデータ取得機能実装**
  - Infrastructure層: `JQuantsFinancialRepository`（API呼び出し）
  - Infrastructure層: `FinancialStatementRepository`（DB保存、UPSERT）
  - UseCase層: `FetchFinancialStatementsUseCase`（日単位分割、差分取得）
  - Jobs層: `fetch_financial_statements.py`（全量取得バッチ）
  - Jobs層: `fetch_daily_financial_statements.py`（差分取得バッチ）

- ✅ **日次ワークフロー統合**
  - `jobs/workflows/daily_data_update.py` 更新
  - 株価取得 → **財務取得（追加）** → テクニカル指標計算

**実装の特徴**:
- ✅ **日単位分割**: jquantsライブラリの並列処理を回避（レート制限対策）
- ✅ **wait=1秒**: 1日ごとに1秒待機（60件/分を確実に回避）
- ✅ **差分取得**: 最新日-1日から取得（遅延開示・訂正に対応）
- ✅ **冪等性**: UPSERT（ON CONFLICT DO UPDATE）で重複回避
- ✅ **進捗保存**: 10日ごとに進捗保存（エラー時の再開対応）

**動作確認**:
- ✅ 全量取得成功: **189,882件**（約10年分、3653日）
- ✅ 所要時間: 79.4分（約1.3秒/日）
- ✅ 差分取得成功: 123件（3日分）
- ✅ 日次ワークフロー成功: 株価4,197件 + 財務123件 + テクニカル4,195件

**使用例**:
```bash
# 全量取得（過去10年分、wait=1秒で約1-2時間）
uv run python backend/jobs/collectors/fetch_financial_statements.py

# テストモード（直近1ヶ月、待機なし）
uv run python backend/jobs/collectors/fetch_financial_statements.py --test

# 差分取得（DBの最新日-1日から自動取得）
uv run python backend/jobs/collectors/fetch_daily_financial_statements.py

# 日次ワークフロー（株価→財務→テクニカル）
uv run python backend/jobs/workflows/daily_data_update.py
```

**実行タイミング**:
- 手動実行: 上記コマンド
- 自動実行: GCP Cloud Scheduler（毎営業日17:30、株価取得後）

**データソース**: `/v2/fins/summary`（財務サマリーAPI）

**レート制限**: 60件/分（株価APIとは独立）

**対象期間**: 2016-07-30 〜 現在（Standardプランの取得可能期間）

**データ量**: **189,882件**（約10年分の決算短信・業績予想修正・配当予想修正）

---

#### ✅ 6-7. ファンダメンタル指標計算バッチ（完了）

**目的**: 財務データから20種類のファンダメンタル指標を計算

**成果物**:
- ✅ **全量計算スクリプト実装完了**
  - `backend/jobs/preprocessors/calculate_fundamental_indicators.py`
  - 株価データ（`stock_prices_daily`）と財務データ（`financial_statements`）をPoint-in-Time結合
  - 株式分割の自動検出・EPS/BPS調整機能
  - 前年同期比（YoY）計算（四半期・通期両対応）

- ✅ **差分計算スクリプト実装完了**
  - `backend/jobs/preprocessors/calculate_daily_fundamental_indicators.py`
  - DBの最新日付から自動差分計算
  - 財務データ全件メモリキャッシュ（約500MB）
  - 冪等性担保（何度実行しても同じ結果）

- ✅ **日次ワークフロー統合完了**
  - `jobs/workflows/daily_data_update.py` にStep 4追加
  - 株価取得 → 財務取得 → テクニカル指標計算 → **ファンダメンタル指標計算（追加）**

**計算指標（20項目）**:
- **バリュエーション（6項目）**: PER（実績）、PBR、PSR、PCFR、予想PER（当期・翌期）
- **収益性（4項目）**: ROE、ROA、営業利益率、純利益率
- **成長性（5項目）**: 売上高/営業利益/純利益/EPS/営業CF成長率（YoY）
- **安全性（1項目）**: 自己資本比率
- **配当（4項目）**: 配当利回り（実績）、配当性向、予想配当利回り（当期・翌期）

**実装の特徴**:
- ✅ **Point-in-Time設計**: 各営業日時点で既に開示されていた最新の財務データのみ使用
- ✅ **株式分割対応**: 時価総額の整合性から分割比率を自動推定、EPS/BPS調整
- ✅ **四半期対応**: 前年同期比（YoY）で正しい成長率計算
- ✅ **会計基準変更対応**: 基準が変わってもYoY計算可能
- ✅ **メモリキャッシュ**: 財務データ全件をメモリに展開（高速化）

**動作確認**:
- ✅ 全量計算成功: **約900万件**（全銘柄×10年分、2019-01-28〜）
- ✅ 差分計算成功: DB最新日+1から自動計算
- ✅ データ精度検証: 松井証券と完全一致（PER 12.2 vs 12.21, PBR 1.00 vs 1.00, 配当利回り 3.26% vs 3.26%）
- ✅ 日次ワークフロー成功: 株価→財務→テクニカル→ファンダメンタルの4ステップ完了

**ドキュメント**:
- ✅ `docs/user/calculation-methodology.md` - ユーザー向け計算方法説明
- ✅ `docs/legal/terms-of-service-draft.md` - 利用規約ドラフト（弁護士レビュー必要）
- ✅ `docs/ml/fundamental-indicators-design.md` - 技術詳細（1,132行、既存）

**使用例**:
```bash
# 全量計算（初回のみ）
uv run python backend/jobs/preprocessors/calculate_fundamental_indicators.py

# 差分計算（日次実行）
uv run python backend/jobs/preprocessors/calculate_daily_fundamental_indicators.py

# 日次ワークフロー（株価→財務→テクニカル→ファンダメンタル）
uv run python backend/jobs/workflows/daily_data_update.py
```

**データ量**: **約900万件**（全4444銘柄 × 約2000営業日 × 20項目）

---

#### 6-8. GCPデプロイ

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

#### 7-1. Phase 1（MVP）: 国内データのみでモデル構築

**場所**: `ml/notebooks/`

**開発方針**:
- ✅ **最初はローカル（Jupyter Notebook）で試行錯誤**
- ✅ LightGBMは軽量なのでローカルで十分（GPU不要）
- ✅ 全銘柄×10年データでも数分〜数十分で学習完了
- ❌ GCPは不要（週次再学習の自動化時のみ使用）

**特徴量（169項目）**:
- テクニカル指標: 125項目（移動平均、RSI、MACD等）
- ファンダメンタル指標: 20項目（PER、PBR、ROE等）
- セクター指数: 17項目（J-Quants API）
- TOPIX/日経平均: 2項目
- 信用倍率: 5項目（信用買い残/売り残、倍率、変化率等）

**実装ステップ**:
1. **データ探索**（`01_data_exploration.ipynb`）
   - トヨタ1銘柄で分析
   - 株価・テクニカル・ファンダメンタル指標の可視化
   - 欠損値確認

2. **特徴量エンジニアリング**（`02_feature_engineering.ipynb`）
   - 169項目の相関分析
   - 欠損値処理方針決定
   - 特徴量スケーリング検討

3. **モデル学習・評価**（`03_model_training.ipynb`）
   - **データ分割**:
     - Training: 2016-2022年（6年）
     - Validation: 2023年（1年）
     - Test: 2024年（1年）
   - LightGBMで翌週騰落率予測（回帰）
   - ハイパーパラメータ調整（Validation使用）
   - Test精度評価（RMSE, MAE, R²）

4. **バックテスト**（`04_backtest.ipynb`）
   - **Walk-Forward Validation**（2024年12月〜2025年1月、4週間）
   - Week 1: 2024年12月第1週のデータで予測 → 第2週の結果と比較
   - Week 2-4: 同様に実施
   - **評価指標**:
     - 回帰精度: RMSE, MAE, R²スコア
     - ランキング精度: 予測Top10と実際Top10の一致率
     - 投資パフォーマンス: Top10を買った場合の累積リターン
   - **目標精度**:
     - R²スコア: 0.05以上（株価予測では0.05でも優秀）
     - Top10適中率: 30%以上（ランダムより有意に高い）
     - 累積リターン: TOPIX平均を上回る

5. **Pythonスクリプト化**
   - `ml/training/train_model.py` 作成
   - `ml/evaluation/evaluate_model.py` 作成（評価レポート自動生成）
   - コマンドラインから実行可能に

**Phase 2移行判断**:
- ✅ 目標精度達成 → Phase 2スキップ、運用開始（フェーズ7-2へ）
- ❌ 目標精度未達 → Phase 2実施（海外データ追加で精度向上）

---

#### 7-2. Phase 2（精度向上）: 海外データ追加（オプション）

**実施条件**: Phase 1で目標精度未達の場合のみ

**追加特徴量（+10項目）**:
- 為替: USD/JPY, EUR/JPY, CNY/JPY（3項目）
- 米国株指数: S&P500, Nasdaq, Dow（3項目）
- 商品: WTI原油, 金（2項目）
- ボラティリティ: VIX（1項目）
- 金利: 米国10年債利回り（1項目）

**データソース**:
- Yahoo Finance API（`yfinance` Pythonライブラリ）
- FRED API（米国10年債）

**実装フロー**:
1. `backend/jobs/collectors/fetch_macro_indicators.py` 実装
2. DBテーブル `macro_economic_indicators` 作成
3. 特徴量結合ロジック追加
4. Phase 1と同じ評価方法で精度改善を定量評価
5. 特徴量重要度分析 → 効果が低い特徴量は削除

**所要時間**: 約1日

---

#### 7-3. 週次推論パイプライン

**ファイル**: `backend/jobs/predictors/generate_weekly_predictions.py`

**目的**: 週末に翌週の推奨銘柄（買い/売り Top10）を算出

**実行タイミング**: 毎週土曜朝（Cloud Schedulerで自動実行）

**処理フロー**:
1. 全銘柄の最新特徴量取得（テクニカル + ファンダメンタル + セクター指数）
2. 学習済みモデル（`models/lightgbm_v1.pkl`）で翌週騰落率予測
3. 予測値上位/下位Top10抽出
4. `rounds`, `round_recommendations`に保存
5. 月曜朝のWebサイト表示に反映

---

### 実装優先順位まとめ

**方針**: Phase 1（国内データのみ）で精度評価 → 必要に応じてPhase 2（海外データ追加）

```
✅ 完了:
  1. フェーズ5: ディレクトリリファクタリング完了
  2. フェーズ6-1: J-Quants API仕様調査 + ドキュメント化完了
  3. フェーズ6-2: 銘柄マスタ取得完了（全4444銘柄） 🎉
  4. フェーズ6-3: 株価データ取得完了（10年分、約1100万レコード） 🎉
  5. フェーズ6-4: 日次差分取得実装完了（DDD構造リファクタリング） 🎉
  6. フェーズ6-5: テクニカル指標計算バッチ完了（125項目、約1100万件） 🎉
  7. フェーズ6-6: 財務データ取得完了（189,882件、10年分） 🎉
  8. フェーズ6-7: ファンダメンタル指標計算完了（20項目、約900万件） 🎉
     - Point-in-Time設計実装完了
     - 株式分割自動検出・調整機能完了
     - 松井証券との精度検証完了（完全一致）
     - 差分計算・日次ワークフロー統合完了
     - 計算ルールドキュメント化完了（user/legal）

🎯 次のセッション（Phase 1準備の残り）:
  9. フェーズ6-8: セクター指数取得
     - J-Quants API /v2/indices/topix/daily から取得
     - 17業種 + TOPIX + 日経平均 = 19項目
     - 過去10年分の日次データ
     - DBテーブル `sector_indices_daily` 作成
     - DDD構造実装（Repository/UseCase/Jobs層）
 10. フェーズ6-9: 信用倍率取得（オプション）
     - J-Quants API /v2/markets/margin から取得
     - 信用買い残/売り残、倍率等 5項目
     - Phase 1で169項目にする場合は必須

⏭️ フェーズ7: 機械学習実装（Phase 1 MVP）:
 11. フェーズ7-1: Jupyter Notebookでモデル構築
     - 特徴量169項目（テクニカル125 + ファンダメンタル20 + セクター指数19 + 信用倍率5）
     - Train/Validation/Test分割（2016-2022/2023/2024）
     - Walk-Forward Validation（2024年12月〜2025年1月、4週間）
     - 精度評価 → 目標達成ならPhase 2スキップ
 12. フェーズ7-3: 週次推論パイプライン実装
     - 学習済みモデルで翌週予測
     - 買い/売り推奨Top10抽出
     - `rounds`, `round_recommendations` 保存

⏭️ フェーズ8: 法令遵守対応（重要）:
 13. フェーズ8-1: J-Quants API利用規約対応
     - FE: TradingView Widget統合（株価・チャート表示）
     - BE: 生データ除外（APIレスポンスから株価・財務生データ削除）
     - FE: 計算済み指標のみ表示
 14. フェーズ8-2: 金融商品取引法対応
     - 利用規約・免責事項の整備
     - 投資助言業でないことの明記
     - 弁護士レビュー（必須）

⏭️ フェーズ9: 本番デプロイ:
 15. フェーズ9-1: GCPデプロイ（自動化）
     - Cloud Run Jobs（日次データ更新）
     - Cloud Scheduler（毎営業日17:30）
 16. フェーズ9-2: 運用開始
```

**特徴量の全体像**:

**Phase 1（MVP）**: 169項目
- ✅ **テクニカル指標**: 125項目（移動平均、RSI、MACD等）
- ✅ **ファンダメンタル指標**: 20項目（PER、PBR、ROE等）
- ✅ **セクター指数**: 17項目（J-Quants API）
- ✅ **TOPIX/日経平均**: 2項目
- ✅ **信用倍率**: 5項目（信用買い残/売り残、倍率、変化率等）

**Phase 2（精度向上 - オプション）**: +10項目
- ⏭️ **為替**: USD/JPY, EUR/JPY, CNY/JPY（3項目）
- ⏭️ **米国株指数**: S&P500, Nasdaq, Dow（3項目）
- ⏭️ **商品**: WTI原油, 金（2項目）
- ⏭️ **ボラティリティ**: VIX（1項目）
- ⏭️ **金利**: 米国10年債利回り（1項目）

**将来拡張（Phase 3以降）**:
- ⏭️ **センチメント指標**: 30項目（ニュース、SNS等）
- ⏭️ **イベント指標**: 20項目（決算発表、配当等）

**評価方針**:
- Phase 1で目標精度達成 → 運用開始
- Phase 1で目標精度未達 → Phase 2で海外データ追加
- 目標: R²≥0.05, Top10適中率≥30%, 累積リターン>TOPIX

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

| **docs/batch/jquants-api.md** | J-Quants API V2仕様（Phase別実装方針） | ⭐⭐⭐ |
| **docs/batch/apis/fin-summary.md** | 財務サマリーAPI詳細仕様 | ⭐⭐⭐ |
| **docs/ml/technical-indicators-125.md** | テクニカル指標125項目詳細 | ⭐⭐⭐ |
| **docs/ml/feature-engineering.md** | Phase別特徴量設計（169/189/249項目） | ⭐⭐⭐ |

### ⏳ 未作成（実装フェーズで必要になったら作成）

- docs/architecture/system-architecture.md
- docs/backend/api-specification.md
- docs/batch/apis/investor-types.md（投資部門別情報API）
- docs/batch/apis/indices.md（指数四本値API）
- docs/batch/apis/margin-interest.md（信用取引週末残高API）
- docs/infrastructure/deployment.md

---

## 参考情報

### 参考プロジェクト

- **jobsan** (`/Users/hh/dev/github/jobsan`) - モノレポ構成、DevContainer設定、Backend（FastAPI + DDD）、Frontend（Next.js）の参考

### 参考記事

- [J-QuantsとAIが切り拓く、個人投資家の新境地](https://note.com/noted_jacana411/n/nf45def4f7fba) - システムの発想元

---

## 最終更新

- **日時**: 2026-07-30 昼（フェーズ6-6完了：財務データ取得完了）
- **作業者**: Claude Code
- **ブランチ**: feature/fundamental
- **変更内容**:
  - ✅ **フェーズ6-6完了: 財務データ取得完了（189,882件、10年分）** 🎉
    - DBテーブル作成: `financial_statements`（約110カラム、Alembic管理）
    - DDD構造実装: Repository/UseCase/Jobs層
    - 全量取得完了: 189,882件（79.4分、約1.3秒/日）
    - 差分取得実装: 最新日-1日から取得（遅延開示・訂正対応）
    - レート制限対策: 日単位分割 + wait=1秒（jquantsライブラリの並列処理を回避）

  - ✅ **日次データ更新ワークフロー完成** 🎉
    - `jobs/workflows/daily_data_update.py` 統合完了
    - フロー: 株価取得 → **財務取得（追加）** → テクニカル指標計算
    - 動作確認: 株価4,197件 + 財務123件 + テクニカル4,195件（約6分）

  - ✅ **CLAUDE.md更新**
    - データベース: 8テーブル → 9テーブル（financial_statements追加）
    - ディレクトリ構成更新: workflows/ディレクトリ追加
    - フェーズ6-6セクション: 完了版に更新

- **前回の完了内容**:
  - ✅ フェーズ6-5完了: テクニカル指標計算バッチ完了（約1100万件）
  - ✅ Phase 1特徴量構成確定: 169項目

- **次回セッション**:
  - フェーズ6-7: ファンダメンタル指標計算バッチ（PER, PBR, ROE等 20項目）
  - フェーズ6-8: セクター指数取得（17業種 + TOPIX + 日経平均）
  - フェーズ6-9: 信用倍率取得（オプション、Phase 1で169項目にする場合）
  - その後、フェーズ7: 機械学習実装（Phase 1 MVP）
