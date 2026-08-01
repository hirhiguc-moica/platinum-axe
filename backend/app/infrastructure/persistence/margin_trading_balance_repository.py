"""信用取引週末残高データ永続化リポジトリ

信用取引残高データのDB保存・取得を担当。
"""

from datetime import date

import pandas as pd
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.margin_trading import MarginTradingBalance


class MarginTradingBalanceRepository:
    """信用取引週末残高データ永続化リポジトリ

    PostgreSQLへの信用取引残高データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = MarginTradingBalanceRepository(session)
        >>> inserted = repo.bulk_upsert(df)
        >>> print(inserted)
        4444
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session
        self._valid_stock_codes: set[str] | None = None  # キャッシュ用

    def get_latest_date(self) -> date | None:
        """全銘柄の最新週末日付を取得

        差分取得の開始日を決定するために使用。

        Returns:
            date | None: 最新の週末日付。データが存在しない場合はNone。

        Example:
            >>> repo = MarginTradingBalanceRepository(session)
            >>> latest = repo.get_latest_date()
            >>> print(latest)
            2026-07-26  # 最新の金曜日
        """
        stmt = select(func.max(MarginTradingBalance.date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame) -> int:
        """信用取引残高DataFrameをPostgreSQL UPSERTでDB保存

        J-Quants APIから取得したDataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: J-Quants APIから取得した信用取引残高データ
                カラム: Code, Date, ShrtVol, LongVol, ShrtNegVol, LongNegVol,
                       ShrtStdVol, LongStdVol, IssType

        Returns:
            int: 保存件数（新規追加 + 更新の合計）

        Note:
            - stock_code + date の UNIQUE制約により重複を防止
            - NaN は None に変換される
            - 信用倍率・増減率は後で別途計算する
            - stock_masterに存在しない銘柄コードはスキップ（外部キー制約対策）
        """
        if len(df) == 0:
            return 0

        # DataFrameのコピーを作成（元データを変更しない）
        df_copy = df.copy()

        # stock_masterに存在する銘柄コードのみを取得（初回のみ、キャッシュ）
        if self._valid_stock_codes is None:
            valid_codes_query = select(text("stock_code")).select_from(text("stock_master"))
            valid_codes_result = self.session.execute(valid_codes_query)
            self._valid_stock_codes = {row[0] for row in valid_codes_result}

        # 存在しない銘柄コードをフィルタリング
        original_count = len(df_copy)
        df_copy = df_copy[df_copy["Code"].isin(self._valid_stock_codes)]
        filtered_count = original_count - len(df_copy)

        if filtered_count > 0:
            print(f"   ⚠️  stock_masterに存在しない銘柄コード: {filtered_count}件スキップ")

        if len(df_copy) == 0:
            return 0

        # ShrtVol, LongVol が NULL/NaN のレコードを除外（念のため）
        df_copy = df_copy[df_copy["ShrtVol"].notna() & df_copy["LongVol"].notna()]

        if len(df_copy) == 0:
            return 0

        # NaN を None に置換（一括処理）
        df_copy = df_copy.where(pd.notna(df_copy), None)

        # Date列を date 型に変換
        df_copy["Date"] = pd.to_datetime(df_copy["Date"]).dt.date

        # カラム名をDBカラム名にマッピング
        df_copy = df_copy.rename(
            columns={
                "Code": "stock_code",
                "Date": "date",
                "ShrtVol": "short_vol",
                "LongVol": "long_vol",
                "ShrtNegVol": "short_neg_vol",
                "LongNegVol": "long_neg_vol",
                "ShrtStdVol": "short_std_vol",
                "LongStdVol": "long_std_vol",
                "IssType": "iss_type",
            }
        )

        # int型に変換（NaN対応）
        int_columns = ["short_vol", "long_vol", "short_neg_vol", "long_neg_vol", "short_std_vol", "long_std_vol"]
        for col in int_columns:
            if col in df_copy.columns:
                df_copy[col] = df_copy[col].apply(lambda x: int(x) if pd.notna(x) and x is not None else 0)

        # 計算項目は初期値NULL（後で計算）
        df_copy["margin_ratio"] = None
        df_copy["long_vol_change"] = None
        df_copy["short_vol_change"] = None
        df_copy["long_vol_change_rate"] = None
        df_copy["short_vol_change_rate"] = None

        # 必要なカラムのみ選択
        required_columns = [
            "stock_code",
            "date",
            "short_vol",
            "long_vol",
            "short_neg_vol",
            "long_neg_vol",
            "short_std_vol",
            "long_std_vol",
            "iss_type",
            "margin_ratio",
            "long_vol_change",
            "short_vol_change",
            "long_vol_change_rate",
            "short_vol_change_rate",
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
        # PostgreSQLの65,535パラメータ上限対策: 500件ずつチャンク分割
        # （信用取引残高は17カラム: 500件 × 17 = 8,500パラメータで安全）
        chunk_size = 500
        total_saved = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]

            stmt = insert(MarginTradingBalance).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_margin_trading_balance_code_date",
                set_={
                    # 生データのみ更新
                    "short_vol": stmt.excluded.short_vol,
                    "long_vol": stmt.excluded.long_vol,
                    "short_neg_vol": stmt.excluded.short_neg_vol,
                    "long_neg_vol": stmt.excluded.long_neg_vol,
                    "short_std_vol": stmt.excluded.short_std_vol,
                    "long_std_vol": stmt.excluded.long_std_vol,
                    "iss_type": stmt.excluded.iss_type,
                    # 計算項目は別途計算するため更新しない（計算済み値を保持）
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
