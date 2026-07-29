"""テクニカル指標永続化リポジトリ

テクニカル指標のDB保存・取得を担当（バッチ処理用）。
"""

from datetime import date

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.models.technical_indicator import TechnicalIndicator


class TechnicalIndicatorRepository:
    """テクニカル指標永続化リポジトリ（バッチ処理用）

    PostgreSQLへのテクニカル指標データのUPSERT保存、最新日付取得を提供。

    使用例:
        >>> repo = TechnicalIndicatorRepository(session)
        >>> saved = repo.bulk_upsert(df)
        >>> print(saved)
        19119
    """

    def __init__(self, session: Session):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
        """
        self.session = session

    def get_latest_date(self) -> date | None:
        """全銘柄の最新テクニカル指標日付を取得

        差分計算の開始日を決定するために使用。

        Returns:
            date | None: 最新の日付。データが存在しない場合はNone。

        Example:
            >>> repo = TechnicalIndicatorRepository(session)
            >>> latest = repo.get_latest_date()
            >>> print(latest)
            2026-07-24
        """
        stmt = select(func.max(TechnicalIndicator.date))
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def bulk_upsert(self, df: pd.DataFrame) -> int:
        """テクニカル指標DataFrameをPostgreSQL UPSERTでDB保存

        計算済みのテクニカル指標DataFrameを、DBモデルに合わせて型変換し、
        ON CONFLICT DO UPDATE (UPSERT) で保存する。

        Args:
            df: 計算済みのテクニカル指標データ（pandas DataFrame）
                必須カラム: stock_code, date
                テクニカル指標カラム: 125項目（NaN許容）

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
        df_copy = df_copy.where(pd.notna(df_copy), None)
        # pd.NA を None に置換（nullable Int64型対策: volume_ma_*, obv_*, days_since_*）
        df_copy = df_copy.replace({pd.NA: None})

        # date列を date 型に変換（必要に応じて）
        if not isinstance(df_copy["date"].iloc[0], date):
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
        # PostgreSQLの65,535パラメータ上限対策: 2000件ずつチャンク分割
        chunk_size = 2000
        total_saved = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i : i + chunk_size]

            stmt = insert(TechnicalIndicator).values(chunk)

            # 全カラムのリスト（125項目 + メタ情報）
            update_columns = {
                # 1. 移動平均線
                "ma_5": stmt.excluded.ma_5,
                "ma_10": stmt.excluded.ma_10,
                "ma_25": stmt.excluded.ma_25,
                "ma_50": stmt.excluded.ma_50,
                "ma_75": stmt.excluded.ma_75,
                "ma_100": stmt.excluded.ma_100,
                "ma_200": stmt.excluded.ma_200,
                "ema_5": stmt.excluded.ema_5,
                "ema_12": stmt.excluded.ema_12,
                "ema_26": stmt.excluded.ema_26,
                "ema_50": stmt.excluded.ema_50,
                "ema_200": stmt.excluded.ema_200,
                "wma_20": stmt.excluded.wma_20,
                # 2. 移動平均の派生特徴量
                "deviation_from_ma5": stmt.excluded.deviation_from_ma5,
                "deviation_from_ma25": stmt.excluded.deviation_from_ma25,
                "deviation_from_ma75": stmt.excluded.deviation_from_ma75,
                "deviation_from_ma200": stmt.excluded.deviation_from_ma200,
                "ma_5_25_deviation": stmt.excluded.ma_5_25_deviation,
                "ma_25_75_deviation": stmt.excluded.ma_25_75_deviation,
                "ma_75_200_deviation": stmt.excluded.ma_75_200_deviation,
                "ma_5_slope_5d": stmt.excluded.ma_5_slope_5d,
                "ma_25_slope_5d": stmt.excluded.ma_25_slope_5d,
                "ma_75_slope_10d": stmt.excluded.ma_75_slope_10d,
                "days_since_gc_5_25": stmt.excluded.days_since_gc_5_25,
                "days_since_dc_5_25": stmt.excluded.days_since_dc_5_25,
                "days_since_gc_25_75": stmt.excluded.days_since_gc_25_75,
                "days_since_dc_25_75": stmt.excluded.days_since_dc_25_75,
                "is_perfect_order_bullish": stmt.excluded.is_perfect_order_bullish,
                "is_perfect_order_bearish": stmt.excluded.is_perfect_order_bearish,
                # 3. 騰落率
                "return_1d": stmt.excluded.return_1d,
                "return_3d": stmt.excluded.return_3d,
                "return_5d": stmt.excluded.return_5d,
                "return_10d": stmt.excluded.return_10d,
                "return_20d": stmt.excluded.return_20d,
                "return_60d": stmt.excluded.return_60d,
                "return_120d": stmt.excluded.return_120d,
                "log_return_1d": stmt.excluded.log_return_1d,
                "log_return_5d": stmt.excluded.log_return_5d,
                "log_return_20d": stmt.excluded.log_return_20d,
                # 4. モメンタム系
                "rsi_9": stmt.excluded.rsi_9,
                "rsi_14": stmt.excluded.rsi_14,
                "rsi_25": stmt.excluded.rsi_25,
                "macd": stmt.excluded.macd,
                "macd_signal": stmt.excluded.macd_signal,
                "macd_histogram": stmt.excluded.macd_histogram,
                "stochastic_k": stmt.excluded.stochastic_k,
                "stochastic_d": stmt.excluded.stochastic_d,
                "stochastic_slow_d": stmt.excluded.stochastic_slow_d,
                "roc_12": stmt.excluded.roc_12,
                "roc_25": stmt.excluded.roc_25,
                "momentum_10": stmt.excluded.momentum_10,
                "momentum_20": stmt.excluded.momentum_20,
                "cci_14": stmt.excluded.cci_14,
                "cci_20": stmt.excluded.cci_20,
                "williams_r_14": stmt.excluded.williams_r_14,
                "mfi_14": stmt.excluded.mfi_14,
                "ultimate_oscillator": stmt.excluded.ultimate_oscillator,
                # 5. トレンド指標
                "adx_14": stmt.excluded.adx_14,
                "plus_di_14": stmt.excluded.plus_di_14,
                "minus_di_14": stmt.excluded.minus_di_14,
                "parabolic_sar": stmt.excluded.parabolic_sar,
                "sar_direction": stmt.excluded.sar_direction,
                "tenkan_sen": stmt.excluded.tenkan_sen,
                "kijun_sen": stmt.excluded.kijun_sen,
                "senkou_span_a": stmt.excluded.senkou_span_a,
                "senkou_span_b": stmt.excluded.senkou_span_b,
                "chikou_span": stmt.excluded.chikou_span,
                "kumo_thickness": stmt.excluded.kumo_thickness,
                "is_above_kumo": stmt.excluded.is_above_kumo,
                "is_below_kumo": stmt.excluded.is_below_kumo,
                # 6. ボラティリティ指標
                "bollinger_upper_2sigma": stmt.excluded.bollinger_upper_2sigma,
                "bollinger_middle": stmt.excluded.bollinger_middle,
                "bollinger_lower_2sigma": stmt.excluded.bollinger_lower_2sigma,
                "bollinger_width": stmt.excluded.bollinger_width,
                "bollinger_position": stmt.excluded.bollinger_position,
                "atr_14": stmt.excluded.atr_14,
                "atr_20": stmt.excluded.atr_20,
                "volatility_10d": stmt.excluded.volatility_10d,
                "volatility_20d": stmt.excluded.volatility_20d,
                "volatility_60d": stmt.excluded.volatility_60d,
                "keltner_upper": stmt.excluded.keltner_upper,
                "keltner_middle": stmt.excluded.keltner_middle,
                "keltner_lower": stmt.excluded.keltner_lower,
                # 7. 出来高系
                "volume_ma_5": stmt.excluded.volume_ma_5,
                "volume_ma_10": stmt.excluded.volume_ma_10,
                "volume_ma_20": stmt.excluded.volume_ma_20,
                "volume_ma_60": stmt.excluded.volume_ma_60,
                "volume_ratio_5": stmt.excluded.volume_ratio_5,
                "volume_ratio_20": stmt.excluded.volume_ratio_20,
                "volume_change_1d": stmt.excluded.volume_change_1d,
                "volume_change_5d": stmt.excluded.volume_change_5d,
                "obv": stmt.excluded.obv,
                "obv_ma_20": stmt.excluded.obv_ma_20,
                "vwap": stmt.excluded.vwap,
                "vwma_20": stmt.excluded.vwma_20,
                "cmf_20": stmt.excluded.cmf_20,
                # 8. 価格位置・高値安値
                "high_5d": stmt.excluded.high_5d,
                "low_5d": stmt.excluded.low_5d,
                "high_20d": stmt.excluded.high_20d,
                "low_20d": stmt.excluded.low_20d,
                "high_60d": stmt.excluded.high_60d,
                "low_60d": stmt.excluded.low_60d,
                "high_52w": stmt.excluded.high_52w,
                "low_52w": stmt.excluded.low_52w,
                "price_from_high_5d": stmt.excluded.price_from_high_5d,
                "price_from_low_5d": stmt.excluded.price_from_low_5d,
                "price_from_high_20d": stmt.excluded.price_from_high_20d,
                "price_from_low_20d": stmt.excluded.price_from_low_20d,
                "price_from_high_52w": stmt.excluded.price_from_high_52w,
                "price_from_low_52w": stmt.excluded.price_from_low_52w,
                "price_position_20d": stmt.excluded.price_position_20d,
                "price_position_52w": stmt.excluded.price_position_52w,
                "is_new_high_20d": stmt.excluded.is_new_high_20d,
                "is_new_low_20d": stmt.excluded.is_new_low_20d,
                "is_new_high_52w": stmt.excluded.is_new_high_52w,
                "is_new_low_52w": stmt.excluded.is_new_low_52w,
                # 9. ローソク足パターン
                "is_doji": stmt.excluded.is_doji,
                "is_hammer": stmt.excluded.is_hammer,
                "is_inverted_hammer": stmt.excluded.is_inverted_hammer,
                "is_shooting_star": stmt.excluded.is_shooting_star,
                "is_hanging_man": stmt.excluded.is_hanging_man,
                "consecutive_up_days": stmt.excluded.consecutive_up_days,
                "consecutive_down_days": stmt.excluded.consecutive_down_days,
                "body_size": stmt.excluded.body_size,
                "upper_shadow_ratio": stmt.excluded.upper_shadow_ratio,
                "lower_shadow_ratio": stmt.excluded.lower_shadow_ratio,
                # 10. その他の指標
                "awesome_oscillator": stmt.excluded.awesome_oscillator,
                "aroon_up": stmt.excluded.aroon_up,
                "aroon_down": stmt.excluded.aroon_down,
                "aroon_oscillator": stmt.excluded.aroon_oscillator,
                # メタ情報
                "calculated_at": stmt.excluded.calculated_at,
            }

            # UNIQUE制約による重複時は更新
            stmt = stmt.on_conflict_do_update(
                constraint="uq_technical_indicators_code_date",
                set_=update_columns,
            )

            self.session.execute(stmt)
            total_saved += len(chunk)

        # トランザクション境界は呼び出し側（UseCase）に寄せる
        # ここではflush()のみ実行（commit()しない）
        self.session.flush()

        # 保存件数を返す
        return total_saved
