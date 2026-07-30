"""J-Quants API 財務データ取得リポジトリ

J-Quants APIから財務サマリーデータを取得する責務を持つ。
"""

from datetime import datetime

import pandas as pd

from app.infrastructure.jquants.jquants_client import JQuantsClient


class JQuantsFinancialRepository:
    """J-Quants API 財務データ取得リポジトリ

    J-Quants APIから財務サマリーデータ（決算短信・業績予想・配当予想）を取得し、DataFrameで返す。

    使用例:
        >>> repo = JQuantsFinancialRepository()
        >>> df = repo.fetch_financial_summary_range(
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 31)
        ... )
        >>> print(len(df))
        1234  # 1ヶ月分の決算開示件数
    """

    def __init__(self, api_key: str | None = None):
        """初期化

        Args:
            api_key: J-Quants APIキー。省略時は環境変数JQUANTS_API_KEYから取得。

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.client = JQuantsClient(api_key=api_key)

    def fetch_financial_summary_range(
        self,
        start_date: datetime,
        end_date: datetime,
        stock_code: str | None = None,
    ) -> pd.DataFrame:
        """財務サマリーデータを期間指定で取得

        Args:
            start_date: 開始日（datetime型）
            end_date: 終了日（datetime型）
            stock_code: 銘柄コード（省略時は全銘柄）

        Returns:
            pd.DataFrame: 財務サマリーデータ

        カラム（主要項目のみ記載、全約140項目）:
            - DiscDate (str): 開示日
            - DiscTime (str): 開示時刻
            - Code (str): 銘柄コード
            - TypeOfDocument (str): 開示書類種別
            - CurPerType (str): 会計期間種別（1Q/2Q/3Q/FY等）
            - Sales (float): 売上高（百万円）
            - OP (float): 営業利益（百万円）
            - OdP (float): 経常利益（百万円）
            - NP (float): 当期純利益（百万円）
            - EPS (float): 1株当たり利益（円）
            - BPS (float): 1株当たり純資産（円）
            - FSales, FOP, FNP, FEPS: 当期予想
            - NxFSales, NxFOP, NxFNP, NxFEPS: 翌期予想
            - Div*, FDiv*, NxFDiv*: 配当実績・予想
            - NC*: 非連結データ
            - 他多数（全約140項目）

        Note:
            - レート制限: 60req/分（株価APIとは独立したカウント）
            - 長期間を一度に取得する場合は、月単位で分割すること

        参考:
            - API仕様: docs/batch/apis/fin-summary.md
            - DBテーブル: docs/database/schemas/financial_statements.md
        """
        return self.client.get_fin_summary_range(
            start_dt=start_date,
            end_dt=end_date,
            code=stock_code,
        )

    def fetch_financial_summary_by_date(self, date: str) -> pd.DataFrame:
        """特定日の財務サマリーデータ取得

        Args:
            date: 開示日（YYYY-MM-DD形式）

        Returns:
            pd.DataFrame: 財務サマリーデータ

        使用例:
            >>> repo = JQuantsFinancialRepository()
            >>> df = repo.fetch_financial_summary_by_date("2024-07-29")
            >>> print(len(df))
            42  # 2024-07-29に開示された決算件数
        """
        return self.client.get_fin_summary(date=date)

    def fetch_financial_summary_by_code(self, stock_code: str) -> pd.DataFrame:
        """特定銘柄の全財務サマリーデータ取得

        Args:
            stock_code: 銘柄コード（4桁または5桁）

        Returns:
            pd.DataFrame: 財務サマリーデータ（全期間）

        使用例:
            >>> repo = JQuantsFinancialRepository()
            >>> df = repo.fetch_financial_summary_by_code("7203")  # トヨタ
            >>> print(len(df))
            80  # 過去10年分の四半期決算 (10年 x 4期 x 2 (修正版含む))
        """
        return self.client.get_fin_summary(code=stock_code)
