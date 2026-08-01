"""セクター指数日次データ永続化リポジトリ

指数データのDB保存・取得を担当。
"""

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.sector_index import SectorIndexDaily


class SectorIndexDailyRepository:
    """セクター指数日次データ永続化リポジトリ

    PostgreSQLへの指数データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = SectorIndexDailyRepository(session)
        >>> inserted = repo.bulk_upsert(df, index_code="0000", index_name="TOPIX")
        >>> print(inserted)
        5
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session

    def get_latest_date(self) -> date | None:
        """全指数の最新日付を取得

        差分取得の開始日を決定するために使用。

        Returns:
            date | None: 最新の日付。データが存在しない場合はNone。

        Example:
            >>> repo = SectorIndexDailyRepository(session)
            >>> latest = repo.get_latest_date()
            >>> print(latest)
            2026-07-30
        """
        stmt = select(func.max(SectorIndexDaily.date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame, index_code: str, index_name: str) -> int:
        """指数DataFrameをPostgreSQL UPSERTでDB保存

        J-Quants APIから取得したDataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: J-Quants APIから取得した指数データ
                カラム: Code, Date, O, H, L, C
            index_code: 指数コード（例: "0000", "0080"）
            index_name: 指数名（例: "TOPIX", "食品"）

        Returns:
            int: 保存件数（新規追加 + 更新の合計）

        Note:
            - index_code + date の UNIQUE制約により重複を防止
            - NaN は None に変換される
            - 騰落率（change_rate_*）は後で別途計算する
        """
        if len(df) == 0:
            return 0

        # DataFrameのコピーを作成（元データを変更しない）
        df_copy = df.copy()

        # close が NULL/NaN のレコードを除外（念のため）
        df_copy = df_copy[df_copy["C"].notna()]

        if len(df_copy) == 0:
            return 0

        # NaN を None に置換（一括処理）
        df_copy = df_copy.where(pd.notna(df_copy), None)

        # Date列を date 型に変換
        df_copy["Date"] = pd.to_datetime(df_copy["Date"]).dt.date

        # カラム名をDBカラム名にマッピング
        df_copy = df_copy.rename(
            columns={
                "Code": "code_api",  # 一時的な名前（後でindex_codeに統一）
                "Date": "date",
                "O": "open",
                "H": "high",
                "L": "low",
                "C": "close",
            }
        )

        # index_code, index_nameを追加
        df_copy["index_code"] = index_code
        df_copy["index_name"] = index_name

        # 数値型をDecimalに変換（NaN対応）
        decimal_columns = ["open", "high", "low", "close"]
        for col in decimal_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(
                    lambda x: Decimal(str(x)) if pd.notna(x) and x is not None else None
                )

        # 騰落率は初期値NULL（後で計算）
        df_copy["change_rate_1d"] = None
        df_copy["change_rate_5d"] = None
        df_copy["change_rate_20d"] = None
        df_copy["change_rate_60d"] = None

        # 必要なカラムのみ選択
        required_columns = [
            "index_code",
            "index_name",
            "date",
            "open",
            "high",
            "low",
            "close",
            "change_rate_1d",
            "change_rate_5d",
            "change_rate_20d",
            "change_rate_60d",
        ]
        df_copy = df_copy[required_columns]

        # DataFrameをdict形式に変換（一括変換、高速）
        records = df_copy.to_dict("records")

        # TimestampMixinカラムを除外（自動生成されるため）
        for record in records:
            record.pop("id", None)
            record.pop("created_at", None)
            record.pop("updated_at", None)

        # PostgreSQL UPSERT (SQLAlchemy ORM)
        # PostgreSQLの65,535パラメータ上限対策: 2000件ずつチャンク分割
        chunk_size = 2000
        total_saved = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]

            stmt = insert(SectorIndexDaily).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_sector_indices_daily_code_date",
                set_={
                    # 生データ（OHLC）のみ更新
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    # 騰落率は別途計算するため更新しない（計算済み値を保持）
                    # 更新日時を記録
                    "updated_at": func.CURRENT_TIMESTAMP(),
                },
            )

            self.session.execute(stmt)
            total_saved += len(chunk)

        # トランザクション境界は呼び出し側（UseCase）に寄せる
        # ここではflush()のみ実行（commit()しない）
        self.session.flush()

        # 保存件数を返す
        return total_saved
