"""J-Quants API V2クライアント

公式jquants-api-clientのラッパークラス
"""

import os
from typing import Any

import jquantsapi
import pandas as pd
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()


class JQuantsClient:
    """J-Quants API V2クライアント

    公式クライアント（jquantsapi.ClientV2）のラッパー。
    環境変数からAPIキーを自動取得し、データ取得メソッドを提供。

    使用例:
        >>> client = JQuantsClient()
        >>> df = client.get_equities_master()
        >>> print(len(df))
        4444
    """

    def __init__(self, api_key: str | None = None):
        """初期化

        Args:
            api_key: J-Quants APIキー。省略時は環境変数JQUANTS_API_KEYから取得。

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.api_key = api_key or os.getenv("JQUANTS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "JQUANTS_API_KEY is required. Set it in .env file or pass it as an argument."
            )

        # 公式クライアント初期化（V2）
        self.client = jquantsapi.ClientV2(api_key=self.api_key)

    def get_equities_master(self) -> pd.DataFrame:
        """銘柄マスタ取得

        全上場銘柄の基本情報を取得（ETF・REIT含む約4400銘柄）。

        Returns:
            pd.DataFrame: 銘柄マスタデータ

        カラム:
            - Date (datetime64): 情報適用年月日
            - Code (str): 銘柄コード
            - CoName (str): 会社名
            - CoNameEn (str): 英語名
            - S17 (str): 17業種コード
            - S17Nm (str): 17業種名
            - S33 (str): 33業種コード
            - S33Nm (str): 33業種名
            - ScaleCat (str): 規模区分（TOPIX分類）
            - Mkt (str): 市場コード
            - MktNm (str): 市場名
            - Mrgn (str): 信用区分コード
            - MrgnNm (str): 信用区分名

        参考:
            - API仕様: docs/batch/jquants-api.md
            - DBテーブル: docs/database/schemas/stock_master.md
        """
        return self.client.get_eq_master()

    def get_daily_quotes(self, code: str | None = None, date: str | None = None) -> pd.DataFrame:
        """株価日次データ取得

        Args:
            code: 銘柄コード（省略時は全銘柄）
            date: 取得日（YYYY-MM-DD形式、省略時は最新）

        Returns:
            pd.DataFrame: 株価日次データ

        カラム:
            - Code (str): 銘柄コード
            - Date (datetime64): 日付
            - Open (float): 始値
            - High (float): 高値
            - Low (float): 安値
            - Close (float): 終値
            - Volume (int): 出来高
            - TurnoverValue (float): 売買代金
            - AdjustmentFactor (float): 調整係数

        参考:
            - API仕様: docs/batch/jquants-api.md
            - DBテーブル: docs/database/schemas/stock_prices_daily.md
        """
        if code and date:
            return self.client.get_eq_bars_daily(code=code, date=date)
        elif code:
            return self.client.get_eq_bars_daily(code=code)
        elif date:
            return self.client.get_eq_bars_daily(date=date)
        else:
            return self.client.get_eq_bars_daily()

    def get_fin_summary(self, code: str | None = None, date: str | None = None) -> pd.DataFrame:
        """財務サマリーデータ取得

        Args:
            code: 銘柄コード（省略時は全銘柄）
            date: 開示日（YYYY-MM-DD形式、省略時は最新）

        Returns:
            pd.DataFrame: 財務サマリーデータ

        カラム:
            - DiscDate (str): 開示日
            - DiscTime (str): 開示時刻
            - Code (str): 銘柄コード
            - DiscNo (str): 開示番号
            - TypeOfDocument (str): 開示書類種別
            - CurPerType (str): 会計期間種別
            - Sales, OP, OdP, NP, EPS等: 財務データ（約140項目）

        参考:
            - API仕様: docs/batch/apis/fin-summary.md
            - DBテーブル: docs/database/schemas/financial_statements.md

        レート制限:
            - 60req/分（株価APIとは独立したカウント）
        """
        if code and date:
            return self.client.get_fin_summary(code=code, date=date)
        elif code:
            return self.client.get_fin_summary(code=code)
        elif date:
            return self.client.get_fin_summary(date=date)
        else:
            return self.client.get_fin_summary()

    def get_fin_summary_range(
        self, start_dt: Any, end_dt: Any, code: str | None = None
    ) -> pd.DataFrame:
        """財務サマリーデータ取得（期間指定）

        Args:
            start_dt: 開始日（datetime型）
            end_dt: 終了日（datetime型）
            code: 銘柄コード（省略時は全銘柄）

        Returns:
            pd.DataFrame: 財務サマリーデータ

        注意:
            - 内部で並列処理を行うため、レート制限に注意（60req/分）
            - 長期間を一度に取得する場合は、期間を分割すること
        """
        if code:
            return self.client.get_fin_summary_range(start_dt=start_dt, end_dt=end_dt, code=code)
        else:
            return self.client.get_fin_summary_range(start_dt=start_dt, end_dt=end_dt)

    def get_daily_quotes_range(
        self, start_dt: Any, end_dt: Any, code: str | None = None
    ) -> pd.DataFrame:
        """株価日次データ取得（期間指定）

        Args:
            start_dt: 開始日（datetime型）
            end_dt: 終了日（datetime型）
            code: 銘柄コード（省略時は全銘柄）

        Returns:
            pd.DataFrame: 株価日次データ

        注意:
            - 内部で並列処理を行うため、レート制限に注意
            - 長期間を一度に取得する場合は、期間を分割すること

        参考:
            - API仕様: docs/batch/jquants-api.md#バッチ処理設計のベストプラクティス
        """
        if code:
            return self.client.get_eq_bars_daily_range(start_dt=start_dt, end_dt=end_dt, code=code)
        else:
            return self.client.get_eq_bars_daily_range(start_dt=start_dt, end_dt=end_dt)

    def get_index_bars_daily_range(
        self, code: str | None, start_dt: Any, end_dt: Any
    ) -> pd.DataFrame:
        """指数四本値データ取得（期間指定）

        Args:
            code: 指数コード（例: "0000", "0080"）。Noneの場合は全指数取得。
            start_dt: 開始日（datetime型）
            end_dt: 終了日（datetime型）

        Returns:
            pd.DataFrame: 指数四本値データ

        カラム:
            - Code (str): 指数コード
            - Date (datetime64): 日付
            - O (float): 始値
            - H (float): 高値
            - L (float): 安値
            - C (float): 終値

        レート制限:
            - 60req/分（株価APIとは独立したカウント）

        参考:
            - API仕様: docs/batch/apis/indices.md
            - DBテーブル: docs/database/schemas/sector_indices_daily.md (未作成)

        Note:
            - jquantsapi公式クライアントのget_idx_bars_dailyがgreenletエラーを起こすため、
              直接HTTPリクエストを送る実装に変更
        """
        # 直接HTTPリクエストを送る（greenletエラー回避）
        from_date = start_dt.strftime("%Y-%m-%d")
        to_date = end_dt.strftime("%Y-%m-%d")

        # J-Quants API v2のエンドポイント
        url = f"{self.client.JQUANTS_API_BASE}/indices/bars/daily"

        # 1日のみの場合はdateパラメータを使用（全指数取得に必須）
        if from_date == to_date:
            params = {"date": from_date}
            # codeが指定されている場合は追加
            if code is not None:
                params["code"] = code
        else:
            # 期間指定の場合はfrom/toとcodeを使用
            params = {
                "code": code,
                "from": from_date,
                "to": to_date,
            }

        # HTTPリクエストを送信（ページネーション対応）
        all_data = []
        while True:
            resp = self.client._get(url, params=params)
            payload = resp.json()

            batch = payload.get("data", [])
            if isinstance(batch, list):
                all_data.extend(batch)

            # ページネーションキーがなければ終了
            pagination_key = payload.get("pagination_key")
            if not pagination_key:
                break
            params["pagination_key"] = pagination_key

        # DataFrameに変換
        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        # Date列をdatetimeに変換
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df

    def get_margin_interest_range(
        self,
        code: str | None,
        start_dt: Any,
        end_dt: Any,
    ) -> pd.DataFrame:
        """信用取引週末残高データを期間指定で取得

        Args:
            code: 銘柄コード（例: "7203"）。Noneの場合は全銘柄取得。
            start_dt: 開始日（datetime型）
            end_dt: 終了日（datetime型）

        Returns:
            pd.DataFrame: 信用取引週末残高データ

        カラム:
            - Code (str): 銘柄コード
            - Date (datetime64): 週末日付（通常金曜日）
            - ShrtVol (int): 売合計信用残高
            - LongVol (int): 買合計信用残高
            - ShrtNegVol (int): 一般信用取引売残高
            - LongNegVol (int): 一般信用取引買残高
            - ShrtStdVol (int): 制度信用取引売残高
            - LongStdVol (int): 制度信用取引買残高
            - IssType (str): 銘柄区分（1:信用、2:貸借、3:その他）

        レート制限:
            - 60req/分（株価APIとは独立したカウント）

        参考:
            - API仕様: https://jpx-jquants.com/ja/spec/mkt-margin-int
            - DBテーブル: margin_trading_balance

        Note:
            - 週末時点のデータ（通常金曜日）
            - 年末年始など営業日が2日以下の週はデータなし
        """
        # 直接HTTPリクエストを送る（greenletエラー回避）
        from_date = start_dt.strftime("%Y-%m-%d")
        to_date = end_dt.strftime("%Y-%m-%d")

        # J-Quants API v2のエンドポイント
        url = f"{self.client.JQUANTS_API_BASE}/markets/margin-interest"

        # ⚠️ このAPIは期間指定（from/to）の場合、codeパラメータが必須
        # 全銘柄取得する場合は、dateパラメータ（1日指定）のみ使用可能
        # そのため、期間指定の場合は日ごとにループで取得する必要がある

        # 1日のみの場合
        if from_date == to_date:
            params = {"date": from_date}
            # codeが指定されている場合は追加
            if code is not None:
                params["code"] = code
        else:
            # 期間指定 + 銘柄指定の場合のみ from/to が使える
            if code is not None:
                params = {
                    "code": code,
                    "from": from_date,
                    "to": to_date,
                }
            else:
                # 全銘柄取得の場合は、日ごとにループで取得（呼び出し側で制御）
                # ここでは1日のみの取得として扱う
                params = {"date": from_date}

        # HTTPリクエストを送信（ページネーション対応）
        all_data = []
        while True:
            resp = self.client._get(url, params=params)
            payload = resp.json()

            batch = payload.get("data", [])
            if isinstance(batch, list):
                all_data.extend(batch)

            # ページネーションキーがなければ終了
            pagination_key = payload.get("pagination_key")
            if not pagination_key:
                break
            params["pagination_key"] = pagination_key

        # DataFrameに変換
        if not all_data:
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        # Date列をdatetimeに変換
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df
