# データベース全体構成

## 概要

プラチナの斧（platinum-axe）のデータベースは、**4層のLayer構造**で設計されています。

```
Layer 1: Raw Data（J-Quants APIから取得した生データ）
  ↓
Layer 2: Derived Data（計算で生成した特徴量）
  ↓
Layer 3: Feature Store（機械学習用に統合された特徴量）
  ↓
Layer 4: Prediction & Result（予測結果・ラウンド推奨）
```

### 設計原則

✅ **J-Quants APIから取得した全データをDBに格納する**

- API依存の低減（過去データ再取得不要）
- パフォーマンス向上（DBクエリの方が高速）
- データ整合性の保証
- APIコスト削減（レート制限対策）

---

## テーブル一覧サマリー

| Layer | テーブル数 | 説明 |
|-------|----------|------|
| Layer 1 | 13テーブル | J-Quants APIから取得 + マスタデータ |
| Layer 2 | 5テーブル | Layer 1から計算で生成 |
| Layer 3 | 2テーブル | Layer 2を統合 |
| Layer 4 | 3テーブル | 予測・推奨・結果 |
| **合計** | **23テーブル** | |

---

## Layer 1: Raw Data（13テーブル）

### J-Quants APIから取得（11テーブル）

| DBテーブル | J-Quants API | エンドポイント | 更新頻度 | 更新時刻 | 更新ジョブ | ステータス |
|-----------|-------------|--------------|---------|---------|----------|----------|
| `stock_master` | 銘柄マスタ | `/v2/equities/master` | 日次 | - | - | ✅ 実装済み |
| `stock_prices_daily` | 株価四本値 | `/v2/equities/bars/daily` | 日次 | - | - | ✅ 実装済み |
| `financial_statements` | 財務サマリー | `/v2/fins/summary` | 四半期 | - | - | ❌ 未実装 |
| `investor_types_weekly` | 投資部門別売買 | `/v2/equities/investor-types` | 週次 | - | - | ❌ 未実装 |
| `margin_interest_weekly` | 信用取引週末残高 | `/v2/markets/margin-interest` | 週次 | - | - | ❌ 未実装 |
| `short_ratio_daily` | 業種別空売り比率 | `/v2/markets/short-ratio` | 日次 | - | - | ❌ 未実装 |
| `short_sale_reports` | 空売り残高報告 | `/v2/markets/short-sale-report` | 随時 | - | - | ❌ 未実装 |
| `indices_topix_daily` | TOPIX四本値 | `/v2/indices/bars/daily/topix` | 日次 | - | - | ❌ 未実装 |
| `large_volume_shareholders` | 大量保有報告書 | `/v2/edinet/large-volume-shareholders` | 随時 | - | - | ❌ 未実装 |
| `earnings_calendar` | 決算発表予定日 | `/v2/equities/earnings-calendar` | 随時更新 | - | - | ❌ 未実装 |
| `trading_calendar` | 取引カレンダー | `/v2/markets/calendar` | 年次 | - | - | ❌ 未実装 |

### マスタデータ（2テーブル）

| DBテーブル | データソース | 説明 | 更新頻度 | 更新時刻 | 更新ジョブ | ステータス |
|-----------|------------|------|---------|---------|----------|----------|
| `markets` | 手動管理 | 市場区分マスタ（Prime, Standard, Growth等） | 不定期 | - | - | ✅ 実装済み |
| `sectors` | 手動管理 | 業種マスタ（33業種分類） | 不定期 | - | - | ✅ 実装済み |

---

## Layer 2: Derived Data（5テーブル）

### 計算で生成される特徴量

| DBテーブル | 計算元テーブル | 生成される特徴量 | 計算頻度 | 計算時刻 | 計算ジョブ | ステータス |
|-----------|--------------|----------------|---------|---------|----------|----------|
| `technical_indicators` | `stock_prices_daily` | テクニカル指標（125項目） | 日次 | - | - | ✅ 実装済み（トヨタのみ） |
| `fundamental_indicators` | `financial_statements` | ファンダメンタル指標（20項目） | 四半期 | - | - | ❌ 未実装 |
| `sentiment_indicators` | `investor_types_weekly`<br>`margin_interest_weekly`<br>`short_ratio_daily`<br>`short_sale_reports` | 市場センチメント指標（30項目） | 日次/週次 | - | - | ❌ 未実装 |
| `macro_indicators` | `indices_topix_daily` | マクロ経済指標（10項目） | 日次 | - | - | ❌ 未実装 |
| `event_indicators` | `large_volume_shareholders`<br>`earnings_calendar`<br>`trading_calendar` | イベント指標（20項目） | 日次 | - | - | ❌ 未実装 |

**特徴量合計**: 125 + 20 + 30 + 10 + 20 = **205項目**

---

## Layer 3: Feature Store（2テーブル）

### 機械学習用統合データ

| DBテーブル | 計算元テーブル | 説明 | ステータス |
|-----------|--------------|------|----------|
| `ml_features` | Layer 2の全5テーブル | 全特徴量を統合（205項目） | ❌ 未実装 |
| `ml_training_data` | `ml_features` + `stock_prices_daily` | 学習用データセット（特徴量 + ラベル） | ❌ 未実装 |

---

## Layer 4: Prediction & Result（3テーブル）

### 予測・推奨・結果

| DBテーブル | データソース | 説明 | ステータス |
|-----------|------------|------|----------|
| `rounds` | バッチ処理 | ラウンド情報（週次） | ✅ 実装済み（モックデータ） |
| `round_recommendations` | 機械学習モデル | 推奨銘柄（買い/売り Top10） | ✅ 実装済み（モックデータ） |
| `round_results` | `stock_prices_daily` | ラウンド結果（実績） | ✅ 実装済み（モックデータ） |

---

## データフロー図

```
【週次データ更新フロー】

金曜17:30: J-Quants APIデータ更新
    ↓
金曜18:00: データ取得バッチ実行
    ↓
    ├─> Layer 1: Raw Data 保存
    │    ├─ stock_prices_daily（全銘柄・1日分）
    │    ├─ financial_statements（決算発表銘柄のみ）
    │    ├─ investor_types_weekly（全銘柄・1週分）
    │    ├─ margin_interest_weekly（全銘柄・1週分）
    │    └─ その他
    ↓
金曜19:00: 特徴量計算バッチ実行
    ↓
    ├─> Layer 2: Derived Data 計算
    │    ├─ technical_indicators（テクニカル125項目）
    │    ├─ fundamental_indicators（ファンダメンタル20項目）
    │    ├─ sentiment_indicators（センチメント30項目）
    │    ├─ macro_indicators（マクロ10項目）
    │    └─ event_indicators（イベント20項目）
    ↓
金曜20:00: 特徴量統合
    ↓
    └─> Layer 3: Feature Store
         └─ ml_features（全205項目統合）
    ↓
金曜21:00: 機械学習モデルで予測
    ↓
    └─> Layer 4: Prediction
         ├─ rounds（新ラウンド作成）
         └─ round_recommendations（買い/売り Top10）
    ↓
土曜00:00: Webサイトに公開
```

---

## 各テーブルの詳細

### 実装済みテーブル（8テーブル）

各テーブルのCREATE TABLE文、カラム定義、インデックス、ソースコードへのリンク等の詳細は、個別ドキュメントを参照してください：

#### Layer 1 (Raw Data)
- **マスタデータ**
  - [`markets`](./schemas/markets.md) - 市場区分マスタ
  - [`sectors`](./schemas/sectors.md) - 業種マスタ
- **J-Quants API**
  - [`stock_master`](./schemas/stock_master.md) - 銘柄マスタ
  - [`stock_prices_daily`](./schemas/stock_prices_daily.md) - 株価日次データ

#### Layer 2 (Derived Data)
- [`technical_indicators`](./schemas/technical_indicators.md) - テクニカル指標（125項目）

#### Layer 4 (Prediction & Result)
- [`rounds`](./schemas/rounds.md) - ラウンド管理
- [`round_recommendations`](./schemas/round_recommendations.md) - 推奨銘柄
- [`round_results`](./schemas/round_results.md) - ラウンド結果

### 未実装テーブル（15テーブル）

未実装のテーブルは、実装時に個別ドキュメント(`docs/database/schemas/テーブル名.md`)を作成します。

### J-Quants APIの詳細仕様

各APIのエンドポイント、レスポンス形式、レート制限等の詳細は、以下のドキュメントを参照してください：

- [jquants-api.md](../batch/jquants-api.md) - J-Quants API V2仕様書

---

## 実装状況

### ✅ 実装済み（7テーブル）

**Layer 1 (Raw Data)**:
- `markets` - 市場区分マスタ（6件）
- `sectors` - 業種マスタ（33件）
- `stock_master` - 銘柄マスタ（10銘柄のみ）
- `stock_prices_daily` - 株価日次（トヨタ240日分のみ）

**Layer 2 (Derived Data)**:
- `technical_indicators` - テクニカル指標（トヨタ240日分、125項目）

**Layer 4 (Prediction & Result)**:
- `rounds` - ラウンド（32件、モックデータ）
- `round_recommendations` - 推奨銘柄（320件、モックデータ）
- `round_results` - 結果データ（300件、モックデータ）

### ❌ 未実装（16テーブル）

**Layer 1 (Raw Data)**: 9テーブル
- `financial_statements`
- `investor_types_weekly`
- `margin_interest_weekly`
- `short_ratio_daily`
- `short_sale_reports`
- `indices_topix_daily`
- `large_volume_shareholders`
- `earnings_calendar`
- `trading_calendar`

**Layer 2 (Derived Data)**: 4テーブル
- `fundamental_indicators`
- `sentiment_indicators`
- `macro_indicators`
- `event_indicators`

**Layer 3 (Feature Store)**: 2テーブル
- `ml_features`
- `ml_training_data`

---

## 次のステップ

### フェーズ6: J-Quants API連携 + データ蓄積

1. **Layer 1テーブルの追加実装**（9テーブル）
   - Alembicマイグレーション作成
   - J-Quants APIクライアント実装
   - データ取得バッチ実装

2. **Layer 2テーブルの追加実装**（4テーブル）
   - 特徴量計算ロジック実装
   - バッチ処理実装

3. **Layer 3テーブルの実装**（2テーブル）
   - 特徴量統合ロジック実装
   - 学習データセット生成

4. **既存データの拡張**
   - `stock_master`: 10銘柄 → 全銘柄（約3800銘柄）
   - `stock_prices_daily`: トヨタ240日 → 全銘柄×10年分（約2500営業日）
   - `technical_indicators`: トヨタ240日 → 全銘柄×10年分

---

## 更新履歴

- **2026-07-23**: 初版作成（Claude Code）
