"""J-Quants API 信用取引残高データ取得リポジトリ

J-Quants APIから信用取引週末残高データを取得する責務を持つ。
"""

from datetime import datetime

import pandas as pd

from app.infrastructure.jquants.jquants_client import JQuantsClient


class JQuantsMarginRepository:
    """J-Quants API 信用取引残高データ取得リポジトリ

    J-Quants APIから信用取引週末残高データを取得し、DataFrameで返す。

    使用例:
        >>> repo = JQuantsMarginRepository()
        >>> df = repo.fetch_margin_interest_range(
        ...     stock_code=None,  # 全銘柄
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31)
        ... )
        >>> print(len(df))
        17776  # 4444銘柄 × 4週分
    """

    def __init__(self, api_key: str | None = None):
        """初期化

        Args:
            api_key: J-Quants APIキー。省略時は環境変数JQUANTS_API_KEYから取得。

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.client = JQuantsClient(api_key=api_key)

    def fetch_margin_interest_range(
        self,
        stock_code: str | None,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """信用取引週末残高データを期間指定で取得

        Args:
            stock_code: 銘柄コード（例: "7203"）。Noneの場合は全銘柄取得。
            start_date: 開始日（datetime型）
            end_date: 終了日（datetime型）

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

        Note:
            - レート制限: 60req/分（1req/秒）
            - 株価APIとは独立したレート制限
            - 週末時点のデータ（通常金曜日）
            - 年末年始など営業日が2日以下の週はデータなし
        """
        return self.client.get_margin_interest_range(
            code=stock_code,
            start_dt=start_date,
            end_dt=end_date,
        )
