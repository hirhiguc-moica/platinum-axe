# 財務サマリーAPI (/v2/fins/summary) 仕様書

## 概要

**エンドポイント**: `GET /v2/fins/summary`

**用途**: 決算短信のサマリー情報（業績ハイライト）を取得

**レート制限**: 60件/分（プラン共通、独立したレート制限）

**データ期間**: 2008年7月7日〜（Standardプランで10年前まで取得可能）

**公式ドキュメント**: https://jpx-jquants.com/ja/spec/fin-summary

---

## クエリパラメータ

**必須条件**: `code` または `date` のいずれか一つ（または両方）を指定

| パラメータ | 型 | 必須 | 説明 | 例 |
|-----------|-----|------|------|-----|
| code | string | △ | 銘柄コード（4桁または5桁） | `7203` |
| date | string | △ | 開示日付（YYYY-MM-DD形式） | `2024-07-29` |
| cursor | string | - | 差分取得用（Premium限定） | - |
| pagination_key | string | - | ページネーション用 | - |

---

## レスポンスフィールド

### 基本情報

| フィールド | 型 | 説明 | 例 |
|-----------|-----|------|-----|
| DiscDate | string | 開示日（YYYY-MM-DD） | `2024-05-10` |
| Code | string | 銘柄コード（5桁） | `72030` |
| DiscNo | string | 開示番号 | - |
| TypeOfDocument | string | 開示書類種別 | `2QFinancialStatements_Consolidated_JP` |

**TypeOfDocument詳細**: [開示書類種別一覧](#開示書類種別一覧)

### 会計期間

| フィールド | 型 | 説明 |
|-----------|-----|------|
| CurPerType | string | 会計期間種別（1Q/2Q/3Q/FY等） |
| CurPerSt | string | 当期開始日 |
| CurPerEn | string | 当期終了日 |
| CurFYSt | string | 当期会計年度開始日 |
| CurFYEn | string | 当期会計年度終了日 |
| NxtFYSt | string | 翌期会計年度開始日 |
| NxtFYEn | string | 翌期会計年度終了日 |

### 財務実績（連結）

| フィールド | 型 | 説明 | 単位 |
|-----------|-----|------|------|
| Sales | float | 売上高 | 百万円 |
| OP | float | 営業利益 | 百万円 |
| OdP | float | 経常利益 | 百万円 |
| NP | float | 当期純利益 | 百万円 |
| EPS | float | 1株当たり利益（EPS） | 円 |
| DEPS | float | 希薄化後EPS | 円 |
| TA | float | 総資産 | 百万円 |
| Eq | float | 純資産 | 百万円 |
| EqAR | float | 自己資本比率 | % |
| BPS | float | 1株当たり純資産（BPS） | 円 |
| CFO | float | 営業キャッシュフロー | 百万円 |
| CFI | float | 投資キャッシュフロー | 百万円 |
| CFF | float | 財務キャッシュフロー | 百万円 |
| CashEq | float | 現金及び現金同等物 | 百万円 |

### 配当情報

**実績**:
- Div1Q, Div2Q, Div3Q, DivFY, DivAnn: 各期配当金（円）

**予想**:
- FDiv1Q, FDiv2Q, FDiv3Q, FDivFY, FDivAnn: 各期配当金予想（円）

### 非連結データ

連結データと同様の項目に `NC` プレフィックスが付く。

例: `NCSales`, `NCOP`, `NCOdP`, `NCNP`, `NCEPS`, `NCBPS` 等

### その他

| フィールド | 型 | 説明 |
|-----------|-----|------|
| MatChgSub | string | 重要な子会社の異動 |
| SigChgInC | string | 連結範囲の重大な変更（2024/7/22追加） |

---

## 開示書類種別一覧

**参照**: https://jpx-jquants.com/ja/spec/fin-summary/typeofdocument

### 通期決算（FY）

| TypeOfDocument | 連結/非連結 | 会計基準 |
|---------------|-----------|---------|
| FYFinancialStatements_Consolidated_JP | 連結 | 日本基準 |
| FYFinancialStatements_Consolidated_US | 連結 | 米国基準 |
| FYFinancialStatements_Consolidated_IFRS | 連結 | IFRS |
| FYFinancialStatements_Consolidated_JMIS | 連結 | JMIS |
| FYFinancialStatements_Consolidated_Foreign | 連結 | 外国株 |
| FYFinancialStatements_NonConsolidated_JP | 非連結 | 日本基準 |
| FYFinancialStatements_NonConsolidated_IFRS | 非連結 | IFRS |
| FYFinancialStatements_NonConsolidated_Foreign | 非連結 | 外国株 |
| FYFinancialStatements_Consolidated_REIT | REIT | - |

### 四半期決算（1Q/2Q/3Q）

| TypeOfDocument | 四半期 | 連結/非連結 | 会計基準 |
|---------------|--------|-----------|---------|
| 1QFinancialStatements_Consolidated_JP | 第1四半期 | 連結 | 日本基準 |
| 2QFinancialStatements_Consolidated_JP | 第2四半期 | 連結 | 日本基準 |
| 3QFinancialStatements_Consolidated_JP | 第3四半期 | 連結 | 日本基準 |
| 1QFinancialStatements_Consolidated_US | 第1四半期 | 連結 | 米国基準 |
| 2QFinancialStatements_Consolidated_US | 第2四半期 | 連結 | 米国基準 |
| 3QFinancialStatements_Consolidated_US | 第3四半期 | 連結 | 米国基準 |
| 1QFinancialStatements_Consolidated_IFRS | 第1四半期 | 連結 | IFRS |
| 2QFinancialStatements_Consolidated_IFRS | 第2四半期 | 連結 | IFRS |
| 3QFinancialStatements_Consolidated_IFRS | 第3四半期 | 連結 | IFRS |
| （以下、非連結・JMIS・外国株も同様） | - | - | - |

### その他

| TypeOfDocument | 説明 |
|---------------|------|
| OtherPeriodFinancialStatements_* | その他四半期決算短信 |
| DividendForecastRevision | 配当予想の修正 |
| EarnForecastRevision | 業績予想の修正 |
| REITDividendForecastRevision | 分配予想の修正（REIT） |
| REITEarnForecastRevision | 利益予想の修正（REIT） |

---

## Pythonクライアント使用例

### 単一日取得

```python
import jquantsapi
from datetime import datetime
from dateutil import tz

cli = jquantsapi.ClientV2(api_key="YOUR_API_KEY")

# 特定日のデータ取得
df = cli.get_fin_summary(date="2024-07-29")
```

### 期間指定取得

```python
# 期間指定取得（推奨）
start_dt = datetime(2024, 1, 1, tzinfo=tz.gettz("Asia/Tokyo"))
end_dt = datetime(2024, 7, 29, tzinfo=tz.gettz("Asia/Tokyo"))

df = cli.get_fin_summary_range(start_dt=start_dt, end_dt=end_dt)
```

### 銘柄指定取得

```python
# 特定銘柄の全データ取得
df = cli.get_fin_summary(code="7203")
```

---

## 重要な注意事項

### 1. 会計基準による差異

- **日本基準（JP）**: 経常利益（OdP）あり
- **IFRS/米国基準**: 経常利益の概念なし → `OdP` は空欄

### 2. レート制限

- **60件/分**（プラン共通、独立したレート制限）
- 株価データAPI（120件/分）とは別カウント
- 大量取得時は適切な待機時間を設定

### 3. データ更新タイミング

- 決算発表後、順次更新
- リアルタイムではない（数時間〜1日程度のタイムラグあり）

### 4. NULL値の扱い

- 未発表項目、該当なし項目は `NULL` または空欄
- 非連結企業の連結データ、IFRS企業の経常利益等

---

## DB格納時の考慮事項

### 1. 主キー設計

**候補**:
- `(Code, DiscDate, TypeOfDocument)` - 同日に複数の開示がある場合を考慮

### 2. データ型選択

| カラム | DBデータ型 | 理由 |
|--------|-----------|------|
| Sales, OP, OdP, NP 等 | NUMERIC(17, 2) | 百万円単位、桁溢れ防止 |
| EPS, BPS, 配当金 | NUMERIC(10, 2) | 円単位、小数点対応 |
| EqAR（自己資本比率） | NUMERIC(5, 2) | パーセント、0-100% |
| 日付 | DATE | YYYY-MM-DD形式 |
| 文字列 | VARCHAR | 可変長 |

### 3. インデックス設計

**推奨インデックス**:
- `(Code, DiscDate DESC)` - 銘柄別の最新データ取得
- `(DiscDate DESC)` - 日付順ソート
- `(CurPerType)` - 四半期/通期フィルタ

---

## 参考リンク

- **公式仕様書**: https://jpx-jquants.com/ja/spec/fin-summary
- **開示書類種別**: https://jpx-jquants.com/ja/spec/fin-summary/typeofdocument
- **J-Quants API仕様**: https://jpx-jquants.com/ja/spec

---

## 更新履歴

- **2026-07-29**: 初版作成（Claude Code）
