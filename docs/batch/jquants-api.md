# J-Quants API 仕様書（V2）

## 概要

**J-Quants API**は、日本取引所グループ（JPX）が提供する、個人投資家向けの金融データAPI。
株価、財務情報、指数データ等を取得できる。

**公式サイト**: https://jpx-jquants.com/
**公式ドキュメント**: https://jpx-jquants.com/ja/spec
**プラン別API利用可否**: https://jpx-jquants.com/ja/spec/data-spec
**公式Pythonクライアント**: https://github.com/J-Quants/jquants-api-client-python

---

## バージョン情報

- **現行バージョン**: V2（2024年リリース）
- **旧バージョン**: V1（廃止予定）
- **主な変更点**:
  - 認証方式の簡素化（リフレッシュトークン方式 → APIキー方式）
  - レスポンスデータの最適化（カラム名短縮）

---

## プラン比較（本プロジェクトではStandardを使用）

| プラン | 月額料金 | レート制限 | データ期間 | 主な機能 |
|--------|---------|-----------|-----------|---------|
| Free | ¥0 | 5件/分 | 12週間前〜2年12週間前 | 株価日次、財務サマリー（限定） |
| Light | ¥990 | 60件/分 | 過去5年 | Free + 指数データ、投資部門別 |
| **Standard** | **¥3,300** | **120件/分** | **過去10年** | **Light + 信用取引データ、日経225オプション** |
| Premium | ¥33,000 | 500件/分 | 過去20年 | Standard + 分足・ティック、先物・オプション全種 |

**✅ 本プロジェクト契約プラン**: Standard（¥3,300/月）

**データ提供開始日**:
- 株価四本値: 2008年5月7日〜
- 財務情報: 2008年7月7日〜
- 信用取引週末残高: 2012年2月10日〜
- 配当金情報: 2013年2月20日〜

**注意**: Standardプランは「過去10年」までアクセス可能ですが、データ提供開始日より前のデータは存在しません。実質的には2008年5月以降のデータが取得可能です。

---

## 認証方法

### V2 API（APIキー方式）

**APIキー取得方法**:
1. J-Quants APIダッシュボードにログイン
2. APIキーを発行
3. 環境変数 `JQUANTS_API_KEY` に設定

**HTTPヘッダーへの設定**:
```
Authorization: Bearer YOUR_API_KEY
```

**Pythonクライアント使用例**:
```python
import jquantsapi

# 方法1: 直接指定
cli = jquantsapi.ClientV2(api_key="YOUR_API_KEY")

# 方法2: 環境変数から自動取得
cli = jquantsapi.ClientV2()  # JQUANTS_API_KEY を使用
```

**設定ファイル（jquants-api.toml）**:
```toml
[jquants-api-client]
api_key = "YOUR_API_KEY"
```

---

## ベースURL

```
https://api.jquants.com/v2/
```

---

## レート制限

### プラン別レート制限

| プラン | 基本レート制限 |
|--------|--------------|
| Free | 5件/分 |
| Light | 60件/分 |
| **Standard** | **120件/分** |
| Premium | 500件/分 |

### エンドポイント別レート制限

一部のエンドポイントは独立したレート制限を持つ：

| エンドポイント | レート制限 | 備考 |
|--------------|-----------|------|
| `/v2/fins/summary` | 60件/分 | プラン共通 |
| `/v2/fins/details` | 60件/分 | プラン共通 |
| `/v2/equities/bars/minute` | 60件/分 | アドオン |
| `/v2/equities/trades` | 60件/分 | アドオン |
| `/v2/td/*` | 100件/分 | アドオン |

### レート制限超過時の挙動

**HTTPステータスコード**: `429 Too Many Requests`

**ペナルティ**: 大幅に超過した場合、**約5分間アクセス完全遮断**の可能性あり

**推奨対策**:
1. `429`受信時は即座にリトライせず、一定時間待機（例: 60秒）
2. Exponential Backoff（指数バックオフ）の実装
3. レート制限を考慮したバッチ設計（後述）

---

## Standardプランで利用可能なAPI一覧

**参照**: [プラン別API利用可否・データ格納期間](https://jpx-jquants.com/ja/spec/data-spec)

### ファンダメンタル分析用API（Phase別実装方針）

本プロジェクトでは、機械学習モデルの精度向上を段階的に進めるため、Phase 1（MVP）とPhase 2（精度向上）で利用するAPIを分けています。

#### 🎯 **Phase 1（MVP）: 必須実装**

| # | API名 | エンドポイント | データ期間 | 用途 | 優先度 |
|---|------|--------------|-----------|------|--------|
| 1 | 財務情報 | `/v2/fins/summary` | 10年前まで（2008/7/7〜） | PER/PBR/ROE/EPS/BPS等の基礎指標計算 | ⭐⭐⭐ |
| 2 | 投資部門別情報 | `/v2/equities/investor-types` | 10年前まで（2008/1/16〜） | 外国人・機関投資家の売買動向（強力なシグナル） | ⭐⭐⭐ |
| 3 | 指数四本値 | `/v2/indices/bars/daily` | 10年前まで（2008/5/7〜） | セクター指数19項目（17業種 + TOPIX + 日経平均） | ⭐⭐⭐ |
| 4 | 信用取引週末残高 | `/v2/markets/margin-interest` | 10年前まで（2012/2/10〜） | 信用倍率・信用買い残/売り残（株価への強力なシグナル） | ⭐⭐⭐ |

**Phase 1 特徴量合計**: テクニカル125項目 + ファンダメンタル20項目 + セクター指数19項目 + 信用倍率5項目 = **169項目**

#### ⚡ **Phase 2（精度向上）: 追加検討**

Phase 1で目標精度（R²≥0.05, Top10適中率≥30%）未達の場合に実装：

| # | API名 | エンドポイント | データ期間 | 用途 | 優先度 |
|---|------|--------------|-----------|------|--------|
| 5 | 業種別空売り比率 | `/v2/markets/short-ratio` | 10年前まで（2008/11/5〜） | 業種別センチメント、逆張り指標 | ⭐⭐ |
| 6 | 空売り残高報告 | `/v2/markets/short-sale-report` | 10年前まで（2013/11/7〜） | 個別銘柄の空売り圧力 | ⭐⭐ |

**Phase 2 特徴量追加**: +海外マクロ10項目（為替、米国株指数、商品等） + センチメント指標（空売り比率等）

#### 📊 **Phase 3以降（将来拡張）**

| # | API名 | エンドポイント | データ期間 | 用途 | 優先度 |
|---|------|--------------|-----------|------|--------|
| 6 | 日々公表信用取引残高 | `/v2/markets/margin-alert` | 10年前まで（2008/5/8〜） | 日次の信用残高（週次データで代替可能） | ⭐ |
| 7 | 大株主状況（EDINET） | `/v2/edinet/major-shareholders` | 10年前まで（2016/6/1〜） | ガバナンス分析、安定株主比率 | ⭐ |
| 8 | 政策保有株式（EDINET） | `/v2/edinet/cross-shareholdings` | 10年前まで（2020/3/31〜） | 政策保有解消トレンド分析 | ⭐ |
| 9 | 大量保有報告書（EDINET） | `/v2/edinet/large-volume-shareholders` | 10年前まで（2021/7/1〜） | アクティビスト参入検知 | ⭐ |
| 10 | 決算発表予定日 | `/v2/equities/earnings-calendar` | 直近データのみ | イベントドリブン戦略 | ⭐ |

**注意**:
- **配当金情報** (`/v2/fins/dividend`) は **Premiumプランのみ**（Standardでは利用不可）
- **財務諸表詳細** (`/v2/fins/details`) も **Premiumプランのみ**（Standardでは財務サマリーのみ）

---

## APIとDBテーブルの対応表

本プロジェクトで使用するJ-Quants APIと、そのデータを格納するDBテーブルの対応関係を示します。

### 必須API（11種）

| # | API名 | エンドポイント | 格納先DBテーブル | 更新頻度 | 更新時刻 | 更新ジョブ | 優先度 |
|---|------|--------------|----------------|---------|---------|----------|--------|
| 1 | 銘柄マスタ | `/v2/equities/master` | `stock_master` | 日次 | - | - | ⭐⭐⭐ |
| 2 | 株価四本値 | `/v2/equities/bars/daily` | `stock_prices_daily` | 日次 | - | - | ⭐⭐⭐ |
| 3 | 財務サマリー | `/v2/fins/summary` | `financial_statements` | 四半期 | - | - | ⭐⭐⭐ |
| 4 | 投資部門別売買 | `/v2/equities/investor-types` | `investor_types_weekly` | 週次 | - | - | ⭐⭐⭐ |
| 5 | 信用取引週末残高 | `/v2/markets/margin-interest` | `margin_interest_weekly` | 週次 | - | - | ⭐⭐⭐ |
| 6 | 業種別空売り比率 | `/v2/markets/short-ratio` | `short_ratio_daily` | 日次 | - | - | ⭐⭐⭐ |
| 7 | 空売り残高報告 | `/v2/markets/short-sale-report` | `short_sale_reports` | 随時 | - | - | ⭐⭐⭐ |
| 8 | TOPIX四本値 | `/v2/indices/bars/daily/topix` | `indices_topix_daily` | 日次 | - | - | ⭐⭐⭐ |
| 9 | 大量保有報告書 | `/v2/edinet/large-volume-shareholders` | `large_volume_shareholders` | 随時 | - | - | ⭐⭐⭐ |
| 10 | 決算発表予定日 | `/v2/equities/earnings-calendar` | `earnings_calendar` | 随時更新 | - | - | ⭐⭐⭐ |
| 11 | 取引カレンダー | `/v2/markets/calendar` | `trading_calendar` | 年次 | - | - | ⭐⭐⭐ |

### 推奨API（オプション、将来的に追加検討）

| # | API名 | エンドポイント | 格納先DBテーブル | 更新頻度 | 更新時刻 | 更新ジョブ | 備考 |
|---|------|--------------|----------------|---------|---------|----------|------|
| 12 | 日々公表信用残高 | `/v2/markets/margin-alert` | `margin_alert_daily` | 日次 | - | - | 週次データで代替可能 |
| 13 | 日経225等指数 | `/v2/indices/bars/daily` | `indices_daily` | 日次 | - | - | TOPIXで代替可能 |
| 14 | 大株主状況 | `/v2/edinet/major-shareholders` | `major_shareholders` | 四半期 | - | - | 優先度低 |
| 15 | 政策保有株式 | `/v2/edinet/cross-shareholdings` | `cross_shareholdings` | 年次 | - | - | 優先度低 |

**データベース全体構成の詳細**: [database/overview.md](../database/overview.md)

---

## 主要エンドポイント一覧（本プロジェクトで使用）

### 1. 銘柄マスタ取得

**エンドポイント**: `GET /v2/equities/master`

**用途**: 全上場銘柄の基本情報取得

**Pythonクライアント**:
```python
df = cli.get_eq_master()
```

**レスポンス例**（主要カラム）:
- `Code`: 銘柄コード（例: "7203"）
- `CompanyName`: 会社名（例: "トヨタ自動車"）
- `Sector17Code`: 業種コード（17分類）
- `MarketCode`: 市場区分（Prime, Standard, Growth）
- `ScaleCategory`: 規模区分（TOPIX Large70等）

---

### 2. 株価日次データ取得

**エンドポイント**: `GET /v2/equities/bars/daily`

**用途**: 日次OHLC（四本値）+ 出来高データ取得

**Pythonクライアント**:
```python
from datetime import datetime
from dateutil import tz

# 単一日取得
df = cli.get_eq_bars_daily(date="2025-01-15")

# 期間指定取得（推奨）
df = cli.get_eq_bars_daily_range(
    start_dt=datetime(2020, 1, 1, tzinfo=tz.gettz("Asia/Tokyo")),
    end_dt=datetime(2025, 1, 15, tzinfo=tz.gettz("Asia/Tokyo")),
)
```

**レスポンス例**（主要カラム）:
- `Code`: 銘柄コード
- `Date`: 日付（YYYY-MM-DD）
- `Open`: 始値
- `High`: 高値
- `Low`: 安値
- `Close`: 終値
- `Volume`: 出来高
- `TurnoverValue`: 売買代金
- `AdjustmentFactor`: 調整係数（株式分割等）

**注意事項**:
- `_range`メソッドは並列処理でリクエストを送信
- レート制限を超えないよう、適切な期間に分割すること

---

### 3. 財務サマリー取得

**エンドポイント**: `GET /v2/fins/summary`

**用途**: 決算サマリー（業績ハイライト）取得

**Pythonクライアント**:
```python
# 単一日取得
df = cli.get_fin_summary(date="2025-01-15")

# 期間指定取得
df = cli.get_fin_summary_range(
    start_dt=datetime(2020, 1, 1, tzinfo=tz.gettz("Asia/Tokyo")),
    end_dt=datetime(2025, 1, 15, tzinfo=tz.gettz("Asia/Tokyo")),
)
```

**レスポンス例**（主要カラム）:
- `Code`: 銘柄コード
- `DisclosedDate`: 開示日
- `FiscalYear`: 決算年度
- `FiscalQuarter`: 四半期（1Q, 2Q, 3Q, FY）
- `NetSales`: 売上高
- `OperatingProfit`: 営業利益
- `OrdinaryProfit`: 経常利益
- `Profit`: 当期純利益
- `EarningsPerShare`: EPS
- `TotalAssets`: 総資産
- `Equity`: 純資産
- `EquityToAssetRatio`: 自己資本比率
- `BookValuePerShare`: BPS
- `CashFlowsFromOperatingActivities`: 営業CF
- `CashFlowsFromInvestingActivities`: 投資CF
- `CashFlowsFromFinancingActivities`: 財務CF

**レート制限**: 60件/分（プラン共通）

---

### 4. 財務諸表詳細取得

**エンドポイント**: `GET /v2/fins/details`

**用途**: BS/PL/CFの詳細項目取得

**Pythonクライアント**:
```python
df = cli.get_fin_details(code="7203", date="2025-01-15")
```

**レート制限**: 60件/分（プラン共通）

**注意**: Standardプランでは財務詳細は限定的（サマリーのみ推奨）

---

### 5. 配当金情報取得

**エンドポイント**: `GET /v2/fins/dividend`

**用途**: 配当金予想・実績取得

**Pythonクライアント**:
```python
df = cli.get_fin_dividend(code="7203")
```

**レスポンス例**（主要カラム）:
- `Code`: 銘柄コード
- `AnnouncementDate`: 発表日
- `RecordDate`: 権利確定日
- `DividendPerShare`: 1株当たり配当金

---

### 6. 指数データ取得（TOPIX等）

**エンドポイント**: `GET /v2/indices/bars/daily`

**用途**: TOPIX、日経平均等の指数データ取得

**Pythonクライアント**:
```python
# TOPIX
df = cli.get_idx_bars_daily(code="0000")

# 日経平均
df = cli.get_idx_bars_daily(code="0001")
```

**注意**: Lightプラン以上で利用可能

---

## データ形式

### リクエスト

**HTTPメソッド**: `GET`

**共通クエリパラメータ**:
- `date`: 取得日（YYYY-MM-DD形式）
- `code`: 銘柄コード（オプション、指定しない場合は全銘柄）
- `from`: 開始日（YYYY-MM-DD形式）
- `to`: 終了日（YYYY-MM-DD形式）

### レスポンス

**フォーマット**: JSON

**構造**:
```json
{
  "data": [
    {
      "Code": "7203",
      "Date": "2025-01-15",
      "Open": 2500.0,
      "High": 2550.0,
      "Low": 2480.0,
      "Close": 2530.0,
      "Volume": 1000000
    }
  ],
  "pagination_key": "next_page_token"
}
```

**Pythonクライアント使用時**: pandas DataFrame形式で返却

---

## エラーハンドリング

### 主要HTTPステータスコード

| コード | 意味 | 対応方法 |
|--------|------|---------|
| 200 | 成功 | - |
| 400 | リクエスト不正 | パラメータ確認 |
| 401 | 認証失敗 | APIキー確認 |
| 403 | アクセス権限なし | プラン・契約確認 |
| 404 | リソース未存在 | エンドポイント・パラメータ確認 |
| 429 | レート制限超過 | 待機後リトライ（Exponential Backoff） |
| 500 | サーバーエラー | 時間をおいてリトライ |
| 503 | サービス利用不可 | メンテナンス確認 |

### リトライ戦略（推奨実装）

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class RateLimitError(Exception):
    pass

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(RateLimitError)
)
def fetch_with_retry(cli, start_dt, end_dt):
    try:
        return cli.get_eq_bars_daily_range(start_dt=start_dt, end_dt=end_dt)
    except Exception as e:
        if "429" in str(e):
            raise RateLimitError("Rate limit exceeded")
        raise
```

---

## バッチ処理設計のベストプラクティス

### 1. 初回全件データ取得（過去10年分）

**対象期間**: 2015-01-01 〜 2025-01-15（約2500営業日）
**対象銘柄**: 全銘柄（約3800銘柄）
**推定リクエスト数**: 約100〜200リクエスト（並列処理により最適化）
**所要時間**: 約2〜4時間（レート制限: 120件/分）

**実装方針**:
```python
from datetime import datetime, timedelta
from dateutil import tz

# 1年ずつ分割して取得（レート制限対策）
years = [
    (2015, 2016), (2016, 2017), (2017, 2018), (2018, 2019), (2019, 2020),
    (2020, 2021), (2021, 2022), (2022, 2023), (2023, 2024), (2024, 2025)
]

for start_year, end_year in years:
    start_dt = datetime(start_year, 1, 1, tzinfo=tz.gettz("Asia/Tokyo"))
    end_dt = datetime(end_year, 1, 1, tzinfo=tz.gettz("Asia/Tokyo"))

    df = cli.get_eq_bars_daily_range(start_dt=start_dt, end_dt=end_dt)

    # DB保存処理
    save_to_db(df)

    # レート制限対策: 1分待機
    time.sleep(60)
```

**進捗保存機能**:
- 途中でエラーが発生した場合に備え、年単位で進捗を保存
- JSON形式で `{"last_completed_year": 2022}` を保存
- 再開時は最後に完了した年の翌年から再開

**注意**: データ提供開始日（2008年5月7日）より前のデータは存在しないため、実際には2015年以降のデータのみ取得されます。

---

### 2. 日次差分データ取得

**実行タイミング**: 毎営業日 17:30（東証取引終了後）
**対象期間**: 前営業日1日分
**対象銘柄**: 全銘柄（約3800銘柄）
**推定リクエスト数**: 1リクエスト（全銘柄一括取得）
**所要時間**: 数秒〜数十秒

**実装方針**:
```python
from datetime import datetime, timedelta
import jpholiday

def get_previous_business_day():
    """前営業日を取得（土日祝日を除外）"""
    today = datetime.now()
    previous_day = today - timedelta(days=1)

    # 土日祝日をスキップ
    while previous_day.weekday() >= 5 or jpholiday.is_holiday(previous_day):
        previous_day -= timedelta(days=1)

    return previous_day.strftime("%Y-%m-%d")

# 前営業日のデータ取得
date = get_previous_business_day()
df = cli.get_eq_bars_daily(date=date)

# DB保存
save_to_db(df)
```

---

### 3. 財務データ取得

**実行タイミング**: 週次または月次
**レート制限**: 60件/分（プラン共通）
**注意**: 財務データは株価データよりレート制限が厳しいため、別バッチとして実行

**実装方針**:
```python
# 直近1ヶ月の財務サマリー取得
start_dt = datetime.now() - timedelta(days=30)
end_dt = datetime.now()

df = cli.get_fin_summary_range(
    start_dt=start_dt.replace(tzinfo=tz.gettz("Asia/Tokyo")),
    end_dt=end_dt.replace(tzinfo=tz.gettz("Asia/Tokyo"))
)

# レート制限対策: 60秒待機
time.sleep(60)
```

---

## 必要なPythonライブラリ

```bash
# 公式クライアント
pip install jquants-api-client

# 日付処理
pip install python-dateutil jpholiday

# リトライ処理
pip install tenacity

# 非同期処理（オプション）
pip install httpx[http2]
```

または、`pyproject.toml`に追加：

```toml
[tool.uv.dependencies]
jquants-api-client = "^1.5.0"
python-dateutil = "^2.8.2"
jpholiday = "^0.1.9"
tenacity = "^8.2.3"
httpx = {extras = ["http2"], version = "^0.27.0"}
```

---

## セキュリティ

### APIキーの管理

**✅ 推奨**:
- 環境変数 `JQUANTS_API_KEY` に保存
- `.env` ファイルを使用（`.gitignore`に追加）
- GCP Secret Manager等のシークレット管理サービス使用（本番環境）

**❌ 禁止**:
- ソースコードにハードコード
- Gitリポジトリにコミット
- ログ出力

**環境変数設定例**:
```bash
# .env
JQUANTS_API_KEY=your_api_key_here
```

```python
# Pythonコード
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("JQUANTS_API_KEY")
```

---

## GCPデプロイ時の考慮事項

### Cloud Run Jobs設定

**環境変数**:
- `JQUANTS_API_KEY`: Secret Managerから取得

**スケジュール設定（Cloud Scheduler）**:
```
# 日次データ取得: 毎営業日17:30
cron: 30 17 * * 1-5
timezone: Asia/Tokyo
```

**タイムアウト設定**:
- 初回全件取得: 3600秒（1時間）
- 日次差分取得: 300秒（5分）

**リトライ設定**:
- 最大試行回数: 3回
- リトライ間隔: 60秒

---

## 参考リンク

- **公式サイト**: https://jpx-jquants.com/
- **公式ドキュメント**: https://jpx-jquants.com/ja/spec
- **料金プラン**: https://jpx-jquants.com/ja/plan
- **レート制限詳細**: https://jpx-jquants.com/ja/spec/rate-limits
- **エンドポイント一覧**: https://jpx-jquants.com/ja/spec/bulk-list/endpoints
- **公式Pythonクライアント**: https://github.com/J-Quants/jquants-api-client-python
- **V1→V2移行ガイド**: https://jpx-jquants.com/ja/spec/migration-v1-v2

---

## 更新履歴

- **2026-07-23 18:00**: データ期間の誤りを修正（Standard: 過去5年 → **過去10年**、Premium: 過去10年 → **過去20年**）
- **2026-07-23 17:00**: 初版作成（Claude Code）
