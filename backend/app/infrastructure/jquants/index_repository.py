"""J-Quants API 指数データ取得リポジトリ

J-Quants APIから指数データ（TOPIX、TOPIX-17等）を取得する責務を持つ。
"""

from datetime import datetime

import pandas as pd

from app.infrastructure.jquants.jquants_client import JQuantsClient


class JQuantsIndexRepository:
    """J-Quants API 指数データ取得リポジトリ

    J-Quants APIから指数四本値（日次）データを取得し、DataFrameで返す。

    使用例:
        >>> repo = JQuantsIndexRepository()
        >>> df = repo.fetch_index_daily_range(
        ...     index_code="0000",  # TOPIX
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 7)
        ... )
        >>> print(len(df))
        5
    """

    def __init__(self, api_key: str | None = None):
        """初期化

        Args:
            api_key: J-Quants APIキー。省略時は環境変数JQUANTS_API_KEYから取得。

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.client = JQuantsClient(api_key=api_key)

    def fetch_index_daily_range(
        self,
        index_code: str | None,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """指数四本値データを期間指定で取得

        Args:
            index_code: 指数コード（例: "0000", "0080"）。Noneの場合は全指数取得。
            start_date: 開始日（datetime型）
            end_date: 終了日（datetime型）

        Returns:
            pd.DataFrame: 指数四本値データ

        カラム:
            - Code (str): 指数コード
            - Date (datetime64): 日付
            - O (float): 始値
            - H (float): 高値
            - L (float): 安値
            - C (float): 終値

        Note:
            - レート制限: 60req/分（1req/秒）
            - 株価APIとは独立したレート制限
            - 長期間を一度に取得する場合は、適切な待機時間を設けること
            - index_code=Noneで全38指数をまとめて取得可能
        """
        return self.client.get_index_bars_daily_range(
            code=index_code,
            start_dt=start_date,
            end_dt=end_date,
        )
