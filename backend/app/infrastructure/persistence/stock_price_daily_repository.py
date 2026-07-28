"""株価日次データ永続化リポジトリ

株価データのDB保存・取得を担当。
"""

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.stock_price import StockPriceDaily


class StockPriceDailyRepository:
    """株価日次データ永続化リポジトリ

    PostgreSQLへの株価データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = StockPriceDailyRepository(session)
        >>> inserted = repo.bulk_upsert(df)
        >>> print(inserted)
        19119
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session

    def get_latest_date(self) -> date | None:
        """全銘柄の最新株価日付を取得

        差分取得の開始日を決定するために使用。

        Returns:
            date | None: 最新の日付。データが存在しない場合はNone。

        Example:
            >>> repo = StockPriceDailyRepository(session)
            >>> latest = repo.get_latest_date()
            >>> print(latest)
            2026-07-24
        """
        stmt = select(func.max(StockPriceDaily.date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame) -> int:
        """株価DataFrameをPostgreSQL UPSERTでDB保存

        J-Quants APIから取得したDataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: J-Quants APIから取得した株価データ
                カラム: Code, Date, O, H, L, C, Vo, Va, AdjO, AdjH, AdjL, AdjC,
                       AdjVo, AdjFactor, UL, LL

        Returns:
            int: 保存件数（新規追加 + 更新の合計）

        Note:
            - stock_code + date の UNIQUE制約により重複を防止
            - NaN は None に変換される
            - bool型は J-Quants の文字列 '0'/'1' から変換
            - volume/adjusted_volume は BIGINT (21億超の出来高対応)
        """
        if len(df) == 0:
            return 0

        # DataFrameのコピーを作成（元データを変更しない）
        df_copy = df.copy()

        # NaN を None に置換（一括処理）
        df_copy = df_copy.where(pd.notna(df_copy), None)

        # Date列を date 型に変換
        df_copy["Date"] = pd.to_datetime(df_copy["Date"]).dt.date

        # カラム名をDBカラム名にマッピング
        df_copy = df_copy.rename(
            columns={
                "Code": "stock_code",
                "Date": "date",
                "O": "open",
                "H": "high",
                "L": "low",
                "C": "close",
                "Vo": "volume",
                "Va": "turnover_value",
                "AdjO": "adjusted_open",
                "AdjH": "adjusted_high",
                "AdjL": "adjusted_low",
                "AdjC": "adjusted_close",
                "AdjVo": "adjusted_volume",
                "AdjFactor": "adjustment_factor",
                "UL": "is_upper_limit",
                "LL": "is_lower_limit",
            }
        )

        # 数値型をDecimalに変換（NaN対応）
        decimal_columns = [
            "open",
            "high",
            "low",
            "close",
            "turnover_value",
            "adjusted_open",
            "adjusted_high",
            "adjusted_low",
            "adjusted_close",
            "adjustment_factor",
        ]
        for col in decimal_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(
                    lambda x: Decimal(str(x)) if pd.notna(x) and x is not None else None
                )

        # 整数型に変換（NaN対応）
        int_columns = ["volume", "adjusted_volume"]
        for col in int_columns:
            if col in df_copy.columns:
                # NaNをNoneに置換してからintに変換
                df_copy[col] = df_copy[col].apply(
                    lambda x: int(x) if pd.notna(x) and x is not None else None
                )

        # bool型に変換（文字列 '0'/'1' → bool）
        bool_columns = ["is_upper_limit", "is_lower_limit"]
        for col in bool_columns:
            if col in df_copy.columns:
                # 文字列 '0'/'1' をまずintに変換してからboolに
                # NaNやNoneはFalseに
                df_copy[col] = df_copy[col].apply(
                    lambda x: bool(int(x)) if pd.notna(x) and x is not None and x != "" else False
                )

        # fetched_at を追加
        df_copy["fetched_at"] = datetime.now()

        # 必要なカラムのみ選択
        required_columns = [
            "stock_code",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover_value",
            "adjusted_open",
            "adjusted_high",
            "adjusted_low",
            "adjusted_close",
            "adjusted_volume",
            "adjustment_factor",
            "is_upper_limit",
            "is_lower_limit",
            "fetched_at",
        ]
        df_copy = df_copy[required_columns]

        # DataFrameをdict形式に変換（一括変換、高速）
        records = df_copy.to_dict("records")

        # fetched_atをdatetimeに変換、volumeを確実にintに変換
        fetched_at_value = datetime.now()
        for record in records:
            # fetched_at変換
            if "fetched_at" in record and hasattr(record["fetched_at"], "to_pydatetime"):
                record["fetched_at"] = record["fetched_at"].to_pydatetime()
            else:
                record["fetched_at"] = fetched_at_value

            # volumeを確実にintに変換（NaN対応）
            if "volume" in record:
                val = record["volume"]
                # NaNまたはNoneの場合はNoneに、それ以外はintに変換
                record["volume"] = int(val) if pd.notna(val) and val is not None else None

            if "adjusted_volume" in record:
                val = record["adjusted_volume"]
                record["adjusted_volume"] = int(val) if pd.notna(val) and val is not None else None

            # TimestampMixinカラムを除外（自動生成されるため）
            record.pop("id", None)
            record.pop("created_at", None)
            record.pop("updated_at", None)

        # PostgreSQL UPSERT (SQLAlchemy ORM)
        stmt = insert(StockPriceDaily).values(records)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_stock_prices_daily_code_date",
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "turnover_value": stmt.excluded.turnover_value,
                "adjusted_open": stmt.excluded.adjusted_open,
                "adjusted_high": stmt.excluded.adjusted_high,
                "adjusted_low": stmt.excluded.adjusted_low,
                "adjusted_close": stmt.excluded.adjusted_close,
                "adjusted_volume": stmt.excluded.adjusted_volume,
                "adjustment_factor": stmt.excluded.adjustment_factor,
                "is_upper_limit": stmt.excluded.is_upper_limit,
                "is_lower_limit": stmt.excluded.is_lower_limit,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )

        self.session.execute(stmt)
        self.session.commit()

        # 保存件数を返す
        return len(records)
