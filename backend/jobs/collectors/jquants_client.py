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
                "JQUANTS_API_KEY is required. "
                "Set it in .env file or pass it as an argument."
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

    def get_daily_quotes(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
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
            return self.client.get_eq_bars_daily_range(
                start_dt=start_dt, end_dt=end_dt, code=code
            )
        else:
            return self.client.get_eq_bars_daily_range(start_dt=start_dt, end_dt=end_dt)
