"""信用倍率・増減率計算UseCase

信用取引週末残高データから以下を計算する業務ロジックを提供する。

計算項目:
    - margin_ratio: 信用倍率（買い残 ÷ 売り残）
    - long_vol_change: 買い残前週比増減（株数）
    - short_vol_change: 売り残前週比増減（株数）
    - long_vol_change_rate: 買い残前週比増減率（%）
    - short_vol_change_rate: 売り残前週比増減率（%）

使用例:
    from app.usecase.calculate_margin_ratios_usecase import CalculateMarginRatiosUseCase

    with Session(engine) as session:
        usecase = CalculateMarginRatiosUseCase(session)

        # 差分計算
        result = usecase.execute_incremental()

        # 全量計算
        result = usecase.execute_full()
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


class CalculateMarginRatiosUseCase:
    """信用倍率・増減率計算UseCase"""

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyセッション
        """
        self.session = session

    def execute_incremental(self) -> dict:
        """差分計算を実行する

        最新計算日の翌週から現在までの指標を計算する。

        Returns:
            実行結果の辞書
            {
                'total_calculated': 計算件数,
                'total_updated': 更新件数,
            }
        """
        # margin_ratioの最新計算日を取得
        latest_calculated_query = text("""
            SELECT MAX(date) as latest_calculated_date
            FROM margin_trading_balance
            WHERE margin_ratio IS NOT NULL
        """)

        calc_result = self.session.execute(latest_calculated_query).fetchone()
        latest_calculated_date = calc_result[0] if calc_result and calc_result[0] else None

        if latest_calculated_date is None:
            print("  ⚠️  全量計算が未実施です。先に全量計算を実行してください。")
            return {"total_calculated": 0, "total_updated": 0}

        # 信用取引残高データの最新週末日を取得
        latest_date_query = text("""
            SELECT MAX(date) as latest_date
            FROM margin_trading_balance
        """)

        result = self.session.execute(latest_date_query).fetchone()
        latest_date = result[0] if result and result[0] else None

        if not latest_date:
            print("  ⚠️  データが存在しません")
            return {"total_calculated": 0, "total_updated": 0}

        # 最新計算日の翌週から現在までを対象
        target_start_date = latest_calculated_date + timedelta(days=1)

        print(f"  📅 最新計算週末日: {latest_calculated_date}")
        print(f"  📅 差分対象: {target_start_date} 〜 {latest_date}")

        if target_start_date > latest_date:
            print("  ⚠️  更新対象なし（すべて計算済み）")
            return {"total_calculated": 0, "total_updated": 0}

        # 計算対象開始日の14日前から取得（前週比計算のため）
        data_start_date = target_start_date - timedelta(days=14)

        # 計算実行
        return self._calculate_and_update(
            data_start_date=data_start_date,
            target_start_date=target_start_date,
            latest_date=latest_date,
        )

    def execute_full(self) -> dict:
        """全量計算を実行する

        全レコードの指標を計算する。

        Returns:
            実行結果の辞書
            {
                'total_calculated': 計算件数,
                'total_updated': 更新件数,
            }
        """
        # 全データの日付範囲を取得
        date_range_query = text("""
            SELECT MIN(date) as min_date, MAX(date) as max_date
            FROM margin_trading_balance
        """)

        result = self.session.execute(date_range_query).fetchone()
        if not result or not result[0] or not result[1]:
            print("  ⚠️  データが存在しません")
            return {"total_calculated": 0, "total_updated": 0}

        min_date = result[0]
        max_date = result[1]

        print(f"  📅 計算期間: {min_date} 〜 {max_date}")

        # 計算実行（全期間）
        return self._calculate_and_update(
            data_start_date=min_date,
            target_start_date=min_date,
            latest_date=max_date,
        )

    def _calculate_and_update(
        self,
        data_start_date: date,
        target_start_date: date,
        latest_date: date,
    ) -> dict:
        """指標を計算してDBを更新する（銘柄ごとに分割処理）

        Args:
            data_start_date: データロード開始日
            target_start_date: 計算対象開始日
            latest_date: 最新週末日

        Returns:
            実行結果の辞書
        """
        # 銘柄リストを取得
        print(f"  📋 銘柄リスト取得中...")
        stock_codes_query = text("""
            SELECT DISTINCT stock_code
            FROM margin_trading_balance
            WHERE date >= :start_date
              AND date <= :end_date
            ORDER BY stock_code
        """)

        stock_codes_result = self.session.execute(
            stock_codes_query,
            {"start_date": data_start_date, "end_date": latest_date},
        )
        stock_codes = [row[0] for row in stock_codes_result]

        if len(stock_codes) == 0:
            print("  ⚠️  データが存在しません")
            return {"total_calculated": 0, "total_updated": 0}

        print(f"  📊 対象銘柄数: {len(stock_codes):,}銘柄")
        print(f"  📅 計算期間: {data_start_date} 〜 {latest_date}")
        print("")

        total_calculated = 0
        total_updated = 0

        # 銘柄ごとに処理
        for idx, stock_code in enumerate(stock_codes, 1):
            # 進捗表示（100銘柄ごと）
            if idx % 100 == 0 or idx == len(stock_codes):
                print(f"  処理中... {idx:,}/{len(stock_codes):,}銘柄 ({stock_code})")

            # 1銘柄分のデータを取得
            query = text("""
                SELECT
                    stock_code,
                    date,
                    short_vol,
                    long_vol
                FROM margin_trading_balance
                WHERE stock_code = :stock_code
                  AND date >= :start_date
                  AND date <= :end_date
                ORDER BY date
            """)

            df = pd.read_sql(
                query,
                self.session.bind,
                params={
                    "stock_code": stock_code,
                    "start_date": data_start_date,
                    "end_date": latest_date,
                },
            )

            if len(df) == 0:
                continue

            # Date列をdatetime型に変換
            df["date"] = pd.to_datetime(df["date"])

            # 1. 信用倍率計算（long_vol ÷ short_vol）
            # 異常値を除外: short_volが極端に小さい場合はNULL、倍率が10万倍以上もNULL
            df["margin_ratio"] = df.apply(
                lambda row: (
                    float(row["long_vol"] / row["short_vol"])
                    if row["short_vol"] > 100 and (row["long_vol"] / row["short_vol"]) < 100000
                    else None
                ),
                axis=1,
            )

            # 2. 前週比増減・増減率計算
            df = df.sort_values("date")

            # 1週前（7日前）のデータを取得（shift(1)で1レコード前）
            df["prev_long_vol"] = df["long_vol"].shift(1)
            df["prev_short_vol"] = df["short_vol"].shift(1)

            # 増減（株数）
            df["long_vol_change"] = df["long_vol"] - df["prev_long_vol"]
            df["short_vol_change"] = df["short_vol"] - df["prev_short_vol"]

            # 増減率（%）
            # 異常値を除外: 増減率が±10,000%以上はNULL
            df["long_vol_change_rate"] = df.apply(
                lambda row: (
                    float((row["long_vol_change"] / row["prev_long_vol"]) * 100)
                    if pd.notna(row["prev_long_vol"])
                    and row["prev_long_vol"] > 0
                    and abs((row["long_vol_change"] / row["prev_long_vol"]) * 100) < 10000
                    else None
                ),
                axis=1,
            )
            df["short_vol_change_rate"] = df.apply(
                lambda row: (
                    float((row["short_vol_change"] / row["prev_short_vol"]) * 100)
                    if pd.notna(row["prev_short_vol"])
                    and row["prev_short_vol"] > 0
                    and abs((row["short_vol_change"] / row["prev_short_vol"]) * 100) < 10000
                    else None
                ),
                axis=1,
            )

            # 計算対象のみに絞り込み（target_start_date以降）
            df_target = df[df["date"] >= pd.to_datetime(target_start_date)].copy()

            if len(df_target) == 0:
                continue

            total_calculated += len(df_target)

            # NaN/Inf/NaTを NULL に変換（まず全体を処理）
            df_target = df_target.replace([np.inf, -np.inf, np.nan], None)

            # pandasのNaT（Not a Time）とNaNも確実にNoneに変換
            for col in ["margin_ratio", "long_vol_change", "short_vol_change", "long_vol_change_rate", "short_vol_change_rate"]:
                df_target[col] = df_target[col].replace({np.nan: None, pd.NA: None})

            # numpy型をPython標準型に変換（PostgreSQL互換）
            # margin_ratio, change_rate系 → float or None
            for col in ["margin_ratio", "long_vol_change_rate", "short_vol_change_rate"]:
                df_target[col] = df_target[col].apply(
                    lambda x: float(x) if pd.notna(x) and not isinstance(x, type(None)) else None
                )

            # change系（株数） → int or None
            for col in ["long_vol_change", "short_vol_change"]:
                df_target[col] = df_target[col].apply(
                    lambda x: int(x) if pd.notna(x) and not isinstance(x, type(None)) else None
                )

            # DBを更新
            for _, row in df_target.iterrows():
                # 各値を取得し、nanを確実にNoneに変換
                def safe_value(val):
                    """NaN/None/NAを確実にNoneに変換"""
                    if pd.isna(val) or val is None or (isinstance(val, float) and np.isnan(val)):
                        return None
                    return val

                update_query = text("""
                    UPDATE margin_trading_balance
                    SET
                        margin_ratio = :margin_ratio,
                        long_vol_change = :long_vol_change,
                        short_vol_change = :short_vol_change,
                        long_vol_change_rate = :long_vol_change_rate,
                        short_vol_change_rate = :short_vol_change_rate,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE stock_code = :stock_code
                      AND date = :date
                """)

                self.session.execute(
                    update_query,
                    {
                        "stock_code": row["stock_code"],
                        "date": row["date"].date(),
                        "margin_ratio": safe_value(row["margin_ratio"]),
                        "long_vol_change": safe_value(row["long_vol_change"]),
                        "short_vol_change": safe_value(row["short_vol_change"]),
                        "long_vol_change_rate": safe_value(row["long_vol_change_rate"]),
                        "short_vol_change_rate": safe_value(row["short_vol_change_rate"]),
                    },
                )
                total_updated += 1

            # 100銘柄ごとにコミット
            if idx % 100 == 0:
                self.session.commit()

        # 最終コミット
        self.session.commit()

        print(f"\n  ✅ 計算完了: {total_calculated:,}件")
        print(f"  ✅ DB更新完了: {total_updated:,}件")

        return {"total_calculated": total_calculated, "total_updated": total_updated}
