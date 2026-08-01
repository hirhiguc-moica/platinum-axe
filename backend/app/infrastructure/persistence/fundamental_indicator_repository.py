"""ファンダメンタル指標永続化リポジトリ

ファンダメンタル指標のDB保存・取得を担当（バッチ処理用）。
"""

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.fundamental_indicator import FundamentalIndicator


class FundamentalIndicatorRepository:
    """ファンダメンタル指標永続化リポジトリ（バッチ処理用）

    PostgreSQLへのファンダメンタル指標データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = FundamentalIndicatorRepository(session)
        >>> saved = repo.bulk_upsert(df)
        >>> print(saved)
        4444
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session

    def get_latest_date(self) -> date | None:
        """全銘柄の最新ファンダメンタル指標日付を取得

        差分計算の開始日を決定するために使用。

        Returns:
            date | None: 最新の日付。データが存在しない場合はNone。

        Example:
            >>> repo = FundamentalIndicatorRepository(session)
            >>> latest = repo.get_latest_date()
            >>> print(latest)
            2026-07-30
        """
        stmt = select(func.max(FundamentalIndicator.date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame) -> int:
        """ファンダメンタル指標DataFrameをPostgreSQL UPSERTでDB保存

        計算済みのファンダメンタル指標DataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: 計算済みのファンダメンタル指標データ（pandas DataFrame）
                必須カラム: stock_code, date
                ファンダメンタル指標カラム: 20項目（NaN許容）

        Returns:
            int: 保存件数（新規追加 + 更新の合計）

        Note:
            - stock_code + date の UNIQUE制約により重複を防止
            - NaN は None に変換される
            - calculated_at は自動設定（現在日付）
        """
        if len(df) == 0:
            return 0

        # DataFrameのコピーを作成（元データを変更しない）
        df_copy = df.copy()

        # NaN を None に置換（一括処理）
        # numpy.nan, numpy.inf, pd.NA をすべて None に変換
        df_copy = df_copy.replace([np.nan, np.inf, -np.inf, pd.NA], None)

        # date列を date 型に正規化（Timestamp/datetime/文字列すべて対応）
        df_copy["date"] = pd.to_datetime(df_copy["date"]).dt.date

        # calculated_at を追加（現在日付）
        df_copy["calculated_at"] = date.today()

        # DataFrameをdict形式に変換（一括変換、高速）
        records = df_copy.to_dict("records")

        # 型変換処理（必要に応じて）
        for record in records:
            # TimestampMixinカラムを除外（自動生成されるため）
            record.pop("id", None)
            record.pop("created_at", None)
            record.pop("updated_at", None)

        # PostgreSQL UPSERT (SQLAlchemy ORM)
        # PostgreSQLの65,535パラメータ上限対策: カラム数から安全なチャンクサイズを動的に算出
        max_params = 65000  # PostgreSQL BIND上限65,535から余裕を持って65,000
        num_columns = len(records[0]) if records else 23  # 実際のカラム数（20指標 + stock_code, date, calculated_at）
        chunk_size = max(1, max_params // num_columns)  # 約2826件 (65000 / 23)
        total_saved = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]

            stmt = insert(FundamentalIndicator).values(chunk)

            # 全カラムのリスト（20項目 + メタ情報）
            update_columns = {
                # 1. バリュエーション指標
                "per": stmt.excluded.per,
                "pbr": stmt.excluded.pbr,
                "psr": stmt.excluded.psr,
                "pcfr": stmt.excluded.pcfr,
                "forward_per_fy": stmt.excluded.forward_per_fy,
                "forward_per_nx": stmt.excluded.forward_per_nx,
                # 2. 収益性指標
                "roe": stmt.excluded.roe,
                "roa": stmt.excluded.roa,
                "operating_margin": stmt.excluded.operating_margin,
                "net_margin": stmt.excluded.net_margin,
                # 3. 成長性指標
                "sales_growth_yoy": stmt.excluded.sales_growth_yoy,
                "op_growth_yoy": stmt.excluded.op_growth_yoy,
                "np_growth_yoy": stmt.excluded.np_growth_yoy,
                "eps_growth_yoy": stmt.excluded.eps_growth_yoy,
                "cfo_growth_yoy": stmt.excluded.cfo_growth_yoy,
                # 4. 安全性指標
                "equity_ratio": stmt.excluded.equity_ratio,
                # 5. 配当指標
                "dividend_yield": stmt.excluded.dividend_yield,
                "payout_ratio": stmt.excluded.payout_ratio,
                "forward_div_yield_fy": stmt.excluded.forward_div_yield_fy,
                "forward_div_yield_nx": stmt.excluded.forward_div_yield_nx,
                # メタ情報
                "calculated_at": stmt.excluded.calculated_at,
            }

            # UNIQUE制約による重複時は更新
            stmt = stmt.on_conflict_do_update(
                constraint="uq_fundamental_indicators_code_date",
                set_=update_columns,
            )

            self.session.execute(stmt)
            total_saved += len(chunk)

        # トランザクション境界は呼び出し側（UseCase）に寄せる
        # ここではflush()のみ実行（commit()しない）
        self.session.flush()

        # 保存件数を返す
        return total_saved
