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

## 現在の状態（2026-07-23 午前）

### 環境

- ✅ DevContainer起動中
- ✅ PostgreSQL 15起動中（localhost:5432）
- ✅ Redis 7起動中（localhost:6379）
- ✅ Backend起動中（http://localhost:8000）
- ✅ Frontend起動中（http://localhost:3000）
- ✅ FE⇄BE API疎通確認済み

### データベース

- ✅ 7テーブル作成完了
  - `markets` (市場区分マスタ6件)
  - `sectors` (業種マスタ33件)
  - `stock_master` (銘柄マスタ10件)
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

### ブランチ

`main`

---

## 次のタスク

**✅ フェーズ2完了: 銘柄詳細ページv1完成**
**✅ フェーズ3完了: 過去のラウンド結果ページv1完成**
**✅ フェーズ4完了: 残りのページ追加完了** 🎉

### 🎯 フェーズ5: 実データ連携拡充（現在はモックデータ）

1. 複数銘柄のモックデータ追加（推奨履歴を充実させる）
2. 銘柄マスタの拡充（現在10銘柄 → 100銘柄程度）
3. 株価データの拡充（現在トヨタのみ → 全銘柄）

### フェーズ6: J-Quants API連携 + データ蓄積バッチ

- J-Quants APIクライアント実装
- データ収集バッチ（日次）
- テクニカル指標計算バッチ
- 週次ラウンド結果検証バッチ

### フェーズ7: 機械学習実装（最終フェーズ）

- 特徴量エンジニアリング
- モデル学習・評価
- 週次推論パイプライン

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

- **日時**: 2026-07-23 午後（銘柄検索機能実装完了）
- **作業者**: Claude Code
- **変更内容**:
  - ✅ **銘柄検索機能実装**（Backend API + Frontend コンポーネント）
    - `GET /api/v1/stocks/search` エンドポイント追加（銘柄コード・会社名の部分一致検索）
    - `StockSearch.tsx` コンポーネント作成（オートコンプリート、Debounce 300ms）
    - レスポンシブ対応（PC: Header右側 / SP: ページ本文上部）
    - 市場略称（PR/ST/GR）+ N225/TPXバッジ表示
  - ✅ 推奨履歴チャートのエラー修正（時刻重複問題を解決）
  - ✅ FE/BE基本機能実装完了 🎉
- **次回**: フェーズ5（モックデータ拡充：銘柄数増加、株価データ追加）
