"""J-Quants API 株価データ取得リポジトリ

J-Quants APIから株価データを取得する責務を持つ。
"""

from datetime import datetime

import pandas as pd

from jobs.collectors.jquants_client import JQuantsClient


class JQuantsStockPriceRepository:
    """J-Quants API 株価データ取得リポジトリ

    J-Quants APIから株価日次データを取得し、DataFrameで返す。

    使用例:
        >>> repo = JQuantsStockPriceRepository()
        >>> df = repo.fetch_daily_quotes_range(
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 7)
        ... )
        >>> print(len(df))
        19119
    """

    def __init__(self, api_key: str | None = None):
        """初期化

        Args:
            api_key: J-Quants APIキー。省略時は環境変数JQUANTS_API_KEYから取得。

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.client = JQuantsClient(api_key=api_key)

    def fetch_daily_quotes_range(
        self,
        start_date: datetime,
        end_date: datetime,
        stock_code: str | None = None,
    ) -> pd.DataFrame:
        """株価日次データを期間指定で取得

        Args:
            start_date: 開始日（datetime型）
            end_date: 終了日（datetime型）
            stock_code: 銘柄コード（省略時は全銘柄）

        Returns:
            pd.DataFrame: 株価日次データ

        カラム:
            - Code (str): 銘柄コード
            - Date (datetime64): 日付
            - O (float): 始値（調整前）
            - H (float): 高値（調整前）
            - L (float): 安値（調整前）
            - C (float): 終値（調整前）
            - Vo (int): 出来高（調整前）
            - Va (float): 売買代金
            - AdjO (float): 調整後始値
            - AdjH (float): 調整後高値
            - AdjL (float): 調整後安値
            - AdjC (float): 調整後終値
            - AdjVo (int): 調整後出来高
            - AdjFactor (float): 調整係数
            - UL (str): ストップ高フラグ ('0' or '1')
            - LL (str): ストップ安フラグ ('0' or '1')

        Note:
            - レート制限: 120req/分（2req/秒）
            - 長期間を一度に取得する場合は、週単位で分割すること
        """
        return self.client.get_daily_quotes_range(
            start_dt=start_date,
            end_dt=end_date,
            code=stock_code,
        )
