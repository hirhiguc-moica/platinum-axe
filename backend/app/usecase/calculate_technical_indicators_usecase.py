"""テクニカル指標計算UseCase（リファクタリング版）

株価データからテクニカル指標を計算してDBに保存するビジネスロジック。
全125項目を実装。
"""

import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.stock import StockMaster
from app.domain.models.stock_price import StockPriceDaily
from app.infrastructure.persistence.stock_price_daily_repository import (
    StockPriceDailyRepository,
)
from app.infrastructure.persistence.technical_indicator_repository import (
    TechnicalIndicatorRepository,
)


class CalculateTechnicalIndicatorsUseCase:
    """テクニカル指標計算UseCase

    株価データからテクニカル指標（125項目）を計算してDBに保存する。
    全件計算、差分計算に対応。
    """

    def __init__(
        self,
        session: Session,
        tech_repo: TechnicalIndicatorRepository | None = None,
        stock_price_repo: StockPriceDailyRepository | None = None,
    ):
        """初期化

        Args:
            session: SQLAlchemyの同期セッション
            tech_repo: テクニカル指標リポジトリ（省略時は自動生成）
            stock_price_repo: 株価リポジトリ（省略時は自動生成）
        """
        self.session = session
        self.tech_repo = tech_repo or TechnicalIndicatorRepository(session)
        self.stock_price_repo = stock_price_repo or StockPriceDailyRepository(session)

    def execute_full(
        self,
        start_date: date,
        end_date: date,
        batch_size: int = 100,
        limit_stocks: int | None = None,
    ) -> dict:
        """全件計算モード（期間指定）"""
        print("=" * 80)
        print("🔄 テクニカル指標計算開始（全件計算モード）")
        print("=" * 80)
        print(f"📅 計算期間: {start_date} 〜 {end_date}")
        total_days = (end_date - start_date).days
        print(f"📊 計算日数: {total_days}日")

        start_time = time.time()
        result = self._calculate_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size,
            limit_stocks=limit_stocks,
        )
        elapsed_seconds = time.time() - start_time

        print("\n" + "=" * 80)
        print("🎉 テクニカル指標計算完了!")
        print("=" * 80)
        print(f"📊 処理銘柄数: {result['total_stocks']}銘柄")
        print(f"📊 計算件数: {result['total_calculated']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_stocks": result["total_stocks"],
            "total_calculated": result["total_calculated"],
            "elapsed_seconds": elapsed_seconds,
        }

    def execute_incremental(self, batch_size: int = 100) -> dict:
        """差分計算モード（株価データとテクニカル指標の差分を検出）"""
        print("=" * 80)
        print("🔄 テクニカル指標計算開始（差分計算モード）")
        print("=" * 80)

        # 株価データの最新日付を取得
        stock_latest_date = self.stock_price_repo.get_latest_date()
        if not stock_latest_date:
            print("❌ エラー: 株価データが存在しません。先に株価データを取得してください。")
            return {
                "total_stocks": 0,
                "total_calculated": 0,
                "elapsed_seconds": 0,
                "start_date": None,
                "end_date": None,
            }

        # テクニカル指標の最新日付を取得
        tech_latest_date = self.tech_repo.get_latest_date()

        if tech_latest_date:
            start_date = tech_latest_date + timedelta(days=1)
            print(f"📂 株価データ最新日付: {stock_latest_date}")
            print(f"📂 テクニカル指標最新日付: {tech_latest_date}")
            print(f"📅 計算開始日: {start_date}")
        else:
            # Standardプラン: 現在から10年前
            ten_years_ago = datetime.now().date() - timedelta(days=365 * 10)
            start_date = ten_years_ago
            print(f"📂 株価データ最新日付: {stock_latest_date}")
            print("⚠️  テクニカル指標データが存在しません。初回計算を開始します。")
            print(f"📅 計算開始日: {start_date} （Standardプラン: 現在から10年前）")

        # 終了日は株価データの最新日付（株価データがある範囲内でのみ計算）
        end_date = stock_latest_date
        print(f"📅 計算終了日: {end_date}")

        if start_date > end_date:
            print("\n✅ 差分データはありません（最新です）")
            return {
                "total_stocks": 0,
                "total_calculated": 0,
                "elapsed_seconds": 0,
                "start_date": start_date,
                "end_date": end_date,
            }

        total_days = (end_date - start_date).days
        print(f"📊 計算日数: {total_days}日")

        start_time = time.time()
        result = self._calculate_and_save_loop(
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size,
        )
        elapsed_seconds = time.time() - start_time

        print("\n" + "=" * 80)
        print("🎉 差分テクニカル指標計算完了!")
        print("=" * 80)
        print(f"📊 処理銘柄数: {result['total_stocks']}銘柄")
        print(f"📊 計算件数: {result['total_calculated']:,}件")
        print(f"⏱️  所要時間: {elapsed_seconds:.1f}秒")
        print("=" * 80)

        return {
            "total_stocks": result["total_stocks"],
            "total_calculated": result["total_calculated"],
            "elapsed_seconds": elapsed_seconds,
            "start_date": start_date,
            "end_date": end_date,
        }

    def _calculate_and_save_loop(
        self,
        start_date: date,
        end_date: date,
        batch_size: int,
        limit_stocks: int | None = None,
    ) -> dict:
        """銘柄ごとに分割してテクニカル指標を計算・保存"""
        stmt = select(StockMaster).order_by(StockMaster.stock_code)
        if limit_stocks:
            stmt = stmt.limit(limit_stocks)
        result = self.session.execute(stmt)
        stocks = result.scalars().all()

        total_stocks = len(stocks)
        total_calculated = 0

        print("\n" + "=" * 80)
        print("📥 テクニカル指標計算開始")
        print("=" * 80)
        print(f"📊 処理対象銘柄数: {total_stocks}銘柄")

        try:
            for i in range(0, total_stocks, batch_size):
                batch_stocks = stocks[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total_stocks + batch_size - 1) // batch_size

                print(f"\n📦 バッチ {batch_num}/{total_batches}: {len(batch_stocks)}銘柄処理中...")

                for stock in batch_stocks:
                    # 最長指標（52週高値/安値 = 252営業日）のウォームアップ期間を確保
                    # 252営業日 ÷ 245営業日/年 × 365日/年 ≈ 376暦日 → 余裕を持って450日
                    extended_start_date = start_date - timedelta(days=450)
                    stock_prices = self._fetch_stock_prices(
                        stock.stock_code, extended_start_date, end_date
                    )

                    if stock_prices.empty:
                        continue

                    tech_df = self._calculate_indicators(stock_prices)

                    tech_df = tech_df[
                        (tech_df["date"] >= start_date) & (tech_df["date"] <= end_date)
                    ]

                    if tech_df.empty:
                        continue

                    saved = self.tech_repo.bulk_upsert(tech_df)
                    total_calculated += saved

                # トランザクションをコミット（バッチごと）
                self.session.commit()
                print(f"  ✅ バッチ完了: 累計 {total_calculated:,}件保存済み")

        except Exception as e:
            self.session.rollback()
            print(f"\n❌ エラー発生: {e}")
            import traceback

            traceback.print_exc()
            raise

        return {
            "total_stocks": total_stocks,
            "total_calculated": total_calculated,
        }

    def _fetch_stock_prices(
        self, stock_code: str, start_date: date, end_date: date
    ) -> pd.DataFrame:
        """株価データを取得"""
        stmt = (
            select(StockPriceDaily)
            .where(
                StockPriceDaily.stock_code == stock_code,
                StockPriceDaily.date >= start_date,
                StockPriceDaily.date <= end_date,
            )
            .order_by(StockPriceDaily.date.asc())
        )
        result = self.session.execute(stmt)
        prices = result.scalars().all()

        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame(
            [
                {
                    "stock_code": p.stock_code,
                    "date": p.date,
                    "open": float(p.open) if p.open is not None else None,
                    "high": float(p.high) if p.high is not None else None,
                    "low": float(p.low) if p.low is not None else None,
                    "close": float(p.close) if p.close is not None else None,
                    "volume": p.volume,
                    "adjusted_close": (
                        float(p.adjusted_close) if p.adjusted_close is not None else None
                    ),
                }
                for p in prices
            ]
        )

        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """テクニカル指標を計算（全125項目）

        各カテゴリのメソッドを呼び出して統合する。
        """
        if df.empty:
            return pd.DataFrame()

        # 各カテゴリの計算を並列実行してDataFrameのリストを作成
        dfs_to_concat = [
            df[["stock_code", "date"]],
            self._calculate_moving_averages(df),
            self._calculate_momentum_indicators(df),
            self._calculate_trend_indicators(df),
            self._calculate_volatility_indicators(df),
            self._calculate_volume_indicators(df),
            self._calculate_price_position_indicators(df),
            self._calculate_pattern_indicators(df),
        ]

        # 一度に全てのカラムを結合（パフォーマンス改善）
        result_df = pd.concat(dfs_to_concat, axis=1)

        # NaN/Inf をNoneに変換
        result_df = result_df.replace([np.nan, np.inf, -np.inf], None)

        return result_df

    # ========================================
    # カテゴリ別計算メソッド
    # ========================================

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """1. 移動平均系の計算"""
        result_df = pd.DataFrame(index=df.index)
        close = df["close"]

        # 単純移動平均（SMA）
        result_df["ma_5"] = close.rolling(window=5).mean()
        result_df["ma_10"] = close.rolling(window=10).mean()
        result_df["ma_25"] = close.rolling(window=25).mean()
        result_df["ma_50"] = close.rolling(window=50).mean()
        result_df["ma_75"] = close.rolling(window=75).mean()
        result_df["ma_100"] = close.rolling(window=100).mean()
        result_df["ma_200"] = close.rolling(window=200).mean()

        # 指数移動平均（EMA）
        result_df["ema_5"] = close.ewm(span=5, adjust=False).mean()
        result_df["ema_12"] = close.ewm(span=12, adjust=False).mean()
        result_df["ema_26"] = close.ewm(span=26, adjust=False).mean()
        result_df["ema_50"] = close.ewm(span=50, adjust=False).mean()
        result_df["ema_200"] = close.ewm(span=200, adjust=False).mean()

        # 加重移動平均（WMA）
        weights = np.arange(1, 21)
        result_df["wma_20"] = close.rolling(window=20).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

        # 移動平均からの乖離率（百分率: 10 = 10%乖離）
        result_df["deviation_from_ma5"] = (close / result_df["ma_5"] - 1) * 100
        result_df["deviation_from_ma25"] = (close / result_df["ma_25"] - 1) * 100
        result_df["deviation_from_ma75"] = (close / result_df["ma_75"] - 1) * 100
        result_df["deviation_from_ma200"] = (close / result_df["ma_200"] - 1) * 100

        # 移動平均線同士の乖離率（百分率: 10 = 10%乖離）
        result_df["ma_5_25_deviation"] = (result_df["ma_5"] / result_df["ma_25"] - 1) * 100
        result_df["ma_25_75_deviation"] = (result_df["ma_25"] / result_df["ma_75"] - 1) * 100
        result_df["ma_75_200_deviation"] = (result_df["ma_75"] / result_df["ma_200"] - 1) * 100

        # 移動平均の傾き（百分率: 10 = 5日間で10%上昇）
        result_df["ma_5_slope_5d"] = (result_df["ma_5"] / result_df["ma_5"].shift(5) - 1) * 100
        result_df["ma_25_slope_5d"] = (result_df["ma_25"] / result_df["ma_25"].shift(5) - 1) * 100
        result_df["ma_75_slope_10d"] = (result_df["ma_75"] / result_df["ma_75"].shift(10) - 1) * 100

        # ゴールデンクロス/デッドクロスからの日数
        gc_dc_5_25 = self._calculate_gc_dc_days(result_df["ma_5"], result_df["ma_25"])
        result_df["days_since_gc_5_25"] = gc_dc_5_25["days_since_gc"]
        result_df["days_since_dc_5_25"] = gc_dc_5_25["days_since_dc"]

        gc_dc_25_75 = self._calculate_gc_dc_days(result_df["ma_25"], result_df["ma_75"])
        result_df["days_since_gc_25_75"] = gc_dc_25_75["days_since_gc"]
        result_df["days_since_dc_25_75"] = gc_dc_25_75["days_since_dc"]

        # パーフェクトオーダー判定
        result_df["is_perfect_order_bullish"] = (
            (result_df["ma_5"] > result_df["ma_25"])
            & (result_df["ma_25"] > result_df["ma_75"])
            & (result_df["ma_75"] > result_df["ma_200"])
        )
        result_df["is_perfect_order_bearish"] = (
            (result_df["ma_5"] < result_df["ma_25"])
            & (result_df["ma_25"] < result_df["ma_75"])
            & (result_df["ma_75"] < result_df["ma_200"])
        )

        return result_df

    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """3. モメンタム系の計算"""
        result_df = pd.DataFrame(index=df.index)
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # 騰落率（百分率: 10 = 10%増、※volume_change_*系とは異なり×100している）
        result_df["return_1d"] = close.pct_change(periods=1, fill_method=None) * 100
        result_df["return_3d"] = close.pct_change(periods=3, fill_method=None) * 100
        result_df["return_5d"] = close.pct_change(periods=5, fill_method=None) * 100
        result_df["return_10d"] = close.pct_change(periods=10, fill_method=None) * 100
        result_df["return_20d"] = close.pct_change(periods=20, fill_method=None) * 100
        result_df["return_60d"] = close.pct_change(periods=60, fill_method=None) * 100
        result_df["return_120d"] = close.pct_change(periods=120, fill_method=None) * 100

        # 対数収益率（百分率: 10 = 10%増）
        result_df["log_return_1d"] = np.log(close / close.shift(1)) * 100
        result_df["log_return_5d"] = np.log(close / close.shift(5)) * 100
        result_df["log_return_20d"] = np.log(close / close.shift(20)) * 100

        # RSI
        result_df["rsi_9"] = self._calculate_rsi(close, period=9)
        result_df["rsi_14"] = self._calculate_rsi(close, period=14)
        result_df["rsi_25"] = self._calculate_rsi(close, period=25)

        # MACD（EMAを再計算）
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        result_df["macd"] = ema_12 - ema_26
        result_df["macd_signal"] = result_df["macd"].ewm(span=9, adjust=False).mean()
        result_df["macd_histogram"] = result_df["macd"] - result_df["macd_signal"]

        # ストキャスティクス
        stoch = self._calculate_stochastic(high, low, close)
        result_df["stochastic_k"] = stoch["k"]
        result_df["stochastic_d"] = stoch["d"]
        result_df["stochastic_slow_d"] = stoch["slow_d"]

        # ROC (Rate of Change)（百分率: 10 = 10%変化）
        result_df["roc_12"] = ((close / close.shift(12)) - 1) * 100
        result_df["roc_25"] = ((close / close.shift(25)) - 1) * 100

        # モメンタム
        result_df["momentum_10"] = close - close.shift(10)
        result_df["momentum_20"] = close - close.shift(20)

        # CCI (Commodity Channel Index)
        result_df["cci_14"] = self._calculate_cci(high, low, close, period=14)
        result_df["cci_20"] = self._calculate_cci(high, low, close, period=20)

        # ウィリアムズ%R
        result_df["williams_r_14"] = self._calculate_williams_r(high, low, close, period=14)

        # MFI (Money Flow Index)
        result_df["mfi_14"] = self._calculate_mfi(high, low, close, volume, period=14)

        # Ultimate Oscillator
        result_df["ultimate_oscillator"] = self._calculate_ultimate_oscillator(high, low, close)

        return result_df

    def _calculate_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """2. トレンド系の計算"""
        result_df = pd.DataFrame(index=df.index)
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # ADX (Average Directional Index)
        adx_data = self._calculate_adx(high, low, close, period=14)
        result_df["adx_14"] = adx_data["adx"]
        result_df["plus_di_14"] = adx_data["plus_di"]
        result_df["minus_di_14"] = adx_data["minus_di"]

        # パラボリックSAR
        sar_data = self._calculate_parabolic_sar(high, low)
        result_df["parabolic_sar"] = sar_data["sar"]
        result_df["sar_direction"] = sar_data["direction"]

        # 一目均衡表
        ichimoku = self._calculate_ichimoku(high, low, close)
        result_df["tenkan_sen"] = ichimoku["tenkan_sen"]
        result_df["kijun_sen"] = ichimoku["kijun_sen"]
        result_df["senkou_span_a"] = ichimoku["senkou_span_a"]
        result_df["senkou_span_b"] = ichimoku["senkou_span_b"]
        result_df["chikou_span"] = ichimoku["chikou_span"]
        result_df["kumo_thickness"] = ichimoku["kumo_thickness"]
        result_df["is_above_kumo"] = ichimoku["is_above_kumo"]
        result_df["is_below_kumo"] = ichimoku["is_below_kumo"]

        return result_df

    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """4. ボラティリティ系の計算"""
        result_df = pd.DataFrame(index=df.index)
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # ボリンジャーバンド
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        result_df["bollinger_middle"] = sma_20
        result_df["bollinger_upper_2sigma"] = sma_20 + 2 * std_20
        result_df["bollinger_lower_2sigma"] = sma_20 - 2 * std_20
        # バンド幅（比率: 0.1 = 10%幅、※×100していない）
        result_df["bollinger_width"] = (
            result_df["bollinger_upper_2sigma"] - result_df["bollinger_lower_2sigma"]
        ) / result_df["bollinger_middle"]
        # バンド内の相対位置（0-1: 0=下限、1=上限）
        result_df["bollinger_position"] = (close - result_df["bollinger_lower_2sigma"]) / (
            result_df["bollinger_upper_2sigma"] - result_df["bollinger_lower_2sigma"]
        )

        # ATR
        result_df["atr_14"] = self._calculate_atr(df, period=14)
        result_df["atr_20"] = self._calculate_atr(df, period=20)

        # ヒストリカル・ボラティリティ（年率換算比率: 0.3 = 30%/年）
        result_df["volatility_10d"] = close.pct_change(fill_method=None).rolling(
            window=10
        ).std() * np.sqrt(252)
        result_df["volatility_20d"] = close.pct_change(fill_method=None).rolling(
            window=20
        ).std() * np.sqrt(252)
        result_df["volatility_60d"] = close.pct_change(fill_method=None).rolling(
            window=60
        ).std() * np.sqrt(252)

        # ケルトナーチャネル
        keltner = self._calculate_keltner_channel(close, high, low, period=20)
        result_df["keltner_upper"] = keltner["upper"]
        result_df["keltner_middle"] = keltner["middle"]
        result_df["keltner_lower"] = keltner["lower"]

        return result_df

    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """5. 出来高系の計算"""
        result_df = pd.DataFrame(index=df.index)
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # 出来高移動平均
        result_df["volume_ma_5"] = volume.rolling(window=5).mean().round().astype(pd.Int64Dtype())
        result_df["volume_ma_10"] = volume.rolling(window=10).mean().round().astype(pd.Int64Dtype())
        result_df["volume_ma_20"] = volume.rolling(window=20).mean().round().astype(pd.Int64Dtype())
        result_df["volume_ma_60"] = volume.rolling(window=60).mean().round().astype(pd.Int64Dtype())

        # 出来高比率（倍率: 2.0 = 2倍）
        result_df["volume_ratio_5"] = volume / result_df["volume_ma_5"]
        result_df["volume_ratio_20"] = volume / result_df["volume_ma_20"]

        # 出来高変化率（比率: 0.1 = 10%増、※return_*系とは異なり×100していない）
        result_df["volume_change_1d"] = volume.pct_change(periods=1, fill_method=None)
        result_df["volume_change_5d"] = volume.pct_change(periods=5, fill_method=None)

        # OBV
        result_df["obv"] = (
            (np.sign(close.diff()) * volume).fillna(0).cumsum().round().astype(pd.Int64Dtype())
        )
        result_df["obv_ma_20"] = (
            result_df["obv"].rolling(window=20).mean().round().astype(pd.Int64Dtype())
        )

        # VWAP（20日ローリング）
        result_df["vwap_20d"] = self._calculate_vwap(high, low, close, volume)

        # VWMA (Volume Weighted Moving Average)
        result_df["vwma_20"] = self._calculate_vwma(close, volume, period=20)

        # CMF (Chaikin Money Flow)
        result_df["cmf_20"] = self._calculate_cmf(high, low, close, volume, period=20)

        return result_df

    def _calculate_price_position_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """6. 価格位置系の計算"""
        result_df = pd.DataFrame(index=df.index)
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # 高値・安値
        result_df["high_5d"] = high.rolling(window=5).max()
        result_df["low_5d"] = low.rolling(window=5).min()
        result_df["high_20d"] = high.rolling(window=20).max()
        result_df["low_20d"] = low.rolling(window=20).min()
        result_df["high_60d"] = high.rolling(window=60).max()
        result_df["low_60d"] = low.rolling(window=60).min()
        result_df["high_52w"] = high.rolling(window=252).max()
        result_df["low_52w"] = low.rolling(window=252).min()

        # 高値・安値からの乖離率（百分率: -10 = 高値から10%下落）
        result_df["price_from_high_5d"] = (close / result_df["high_5d"] - 1) * 100
        result_df["price_from_low_5d"] = (close / result_df["low_5d"] - 1) * 100
        result_df["price_from_high_20d"] = (close / result_df["high_20d"] - 1) * 100
        result_df["price_from_low_20d"] = (close / result_df["low_20d"] - 1) * 100
        result_df["price_from_high_52w"] = (close / result_df["high_52w"] - 1) * 100
        result_df["price_from_low_52w"] = (close / result_df["low_52w"] - 1) * 100

        # 価格の相対位置（0-1: 0=安値、1=高値）
        result_df["price_position_20d"] = (close - result_df["low_20d"]) / (
            result_df["high_20d"] - result_df["low_20d"]
        )
        result_df["price_position_52w"] = (close - result_df["low_52w"]) / (
            result_df["high_52w"] - result_df["low_52w"]
        )

        # 新高値・新安値判定
        result_df["is_new_high_20d"] = close >= result_df["high_20d"]
        result_df["is_new_low_20d"] = close <= result_df["low_20d"]
        result_df["is_new_high_52w"] = close >= result_df["high_52w"]
        result_df["is_new_low_52w"] = close <= result_df["low_52w"]

        return result_df

    def _calculate_pattern_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """7. パターン認識系の計算"""
        result_df = pd.DataFrame(index=df.index)
        open_price = df["open"]
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # ローソク足パターン
        candle = self._calculate_candlestick_patterns(open_price, high, low, close)
        result_df["is_doji"] = candle["is_doji"]
        result_df["is_hammer"] = candle["is_hammer"]
        result_df["is_inverted_hammer"] = candle["is_inverted_hammer"]
        result_df["is_shooting_star"] = candle["is_shooting_star"]
        result_df["is_hanging_man"] = candle["is_hanging_man"]

        # 連続陽線・陰線
        result_df["consecutive_up_days"] = candle["consecutive_up_days"]
        result_df["consecutive_down_days"] = candle["consecutive_down_days"]

        # 実体・ヒゲの比率
        result_df["body_size"] = candle["body_size"]
        result_df["upper_shadow_ratio"] = candle["upper_shadow_ratio"]
        result_df["lower_shadow_ratio"] = candle["lower_shadow_ratio"]

        # Awesome Oscillator
        result_df["awesome_oscillator"] = self._calculate_awesome_oscillator(high, low)

        # Aroon Indicator
        aroon = self._calculate_aroon(high, low, period=25)
        result_df["aroon_up"] = aroon["up"]
        result_df["aroon_down"] = aroon["down"]
        result_df["aroon_oscillator"] = aroon["oscillator"]

        return result_df

    # ========================================
    # ヘルパーメソッド
    # ========================================

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """RSI計算"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """ATR計算"""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> dict:
        """ストキャスティクス計算"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d = k.rolling(window=d_period).mean()
        slow_d = d.rolling(window=d_period).mean()
        return {"k": k, "d": d, "slow_d": slow_d}

    def _calculate_cci(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """CCI計算"""
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return (tp - sma_tp) / (0.015 * mad)

    def _calculate_williams_r(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """ウィリアムズ%R計算"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return ((highest_high - close) / (highest_high - lowest_low)) * -100

    def _calculate_mfi(
        self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14
    ) -> pd.Series:
        """MFI計算"""
        tp = (high + low + close) / 3
        raw_mf = tp * volume
        pos_mf = (raw_mf.where(tp > tp.shift(), 0)).rolling(window=period).sum()
        neg_mf = (raw_mf.where(tp < tp.shift(), 0)).rolling(window=period).sum()
        mfr = pos_mf / neg_mf
        return 100 - (100 / (1 + mfr))

    def _calculate_ultimate_oscillator(
        self, high: pd.Series, low: pd.Series, close: pd.Series
    ) -> pd.Series:
        """Ultimate Oscillator計算"""
        bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
        tr = pd.concat([high, close.shift()], axis=1).max(axis=1) - pd.concat(
            [low, close.shift()], axis=1
        ).min(axis=1)
        avg7 = bp.rolling(window=7).sum() / tr.rolling(window=7).sum()
        avg14 = bp.rolling(window=14).sum() / tr.rolling(window=14).sum()
        avg28 = bp.rolling(window=28).sum() / tr.rolling(window=28).sum()
        return ((avg7 * 4) + (avg14 * 2) + avg28) / 7 * 100

    def _calculate_adx(
        self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> dict:
        """ADX計算（Wilderの定義に準拠）"""
        # 上昇幅・下降幅の計算
        high_diff = high.diff()
        low_diff = -low.diff()

        # Wilderの定義：上昇幅 > 下降幅 かつ 上昇幅 > 0 の場合のみ+DM採用、それ以外は0
        # （-DMも同様。同じ日に両方が正になることはない）
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

        # True Range
        tr = pd.concat(
            [high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1
        ).max(axis=1)

        # ATR
        atr = tr.rolling(window=period).mean()

        # +DI, -DI, DX, ADX
        plus_di = (plus_dm.rolling(window=period).mean() / atr) * 100
        minus_di = (minus_dm.rolling(window=period).mean() / atr) * 100
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()

        return {"adx": adx, "plus_di": plus_di, "minus_di": minus_di}

    def _calculate_parabolic_sar(
        self,
        high: pd.Series,
        low: pd.Series,
        af_start: float = 0.02,
        af_increment: float = 0.02,
        af_max: float = 0.2,
    ) -> dict:
        """パラボリックSAR計算

        Args:
            high: 高値シリーズ
            low: 安値シリーズ
            af_start: 加速度因子の初期値（デフォルト: 0.02）
            af_increment: 加速度因子の増分（デフォルト: 0.02）
            af_max: 加速度因子の最大値（デフォルト: 0.2）

        Returns:
            dict: SAR値とトレンド方向（LONG/SHORT）
        """
        length = len(high)
        sar = np.zeros(length)
        direction = np.array(["LONG"] * length, dtype=object)
        ep = np.zeros(length)  # Extreme Point
        af = np.zeros(length)

        # 初期値設定
        sar[0] = low.iloc[0]
        ep[0] = high.iloc[0]
        af[0] = af_start
        direction[0] = "LONG"

        for i in range(1, length):
            # 前日の値をコピー
            sar[i] = sar[i - 1]
            ep[i] = ep[i - 1]
            af[i] = af[i - 1]
            direction[i] = direction[i - 1]

            if direction[i - 1] == "LONG":
                # ロングポジション
                sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])

                # SARが当日の安値を上回った場合、トレンド転換
                if sar[i] > low.iloc[i]:
                    direction[i] = "SHORT"
                    sar[i] = ep[i - 1]  # 前回のEP（最高値）をSARとする
                    ep[i] = low.iloc[i]
                    af[i] = af_start
                else:
                    # トレンド継続
                    if high.iloc[i] > ep[i - 1]:
                        ep[i] = high.iloc[i]
                        af[i] = min(af[i - 1] + af_increment, af_max)

                    # SARは前2日の安値を超えないように調整
                    if i >= 2:
                        sar[i] = min(sar[i], low.iloc[i - 1], low.iloc[i - 2])
                    elif i >= 1:
                        sar[i] = min(sar[i], low.iloc[i - 1])

            else:
                # ショートポジション
                sar[i] = sar[i - 1] - af[i - 1] * (sar[i - 1] - ep[i - 1])

                # SARが当日の高値を下回った場合、トレンド転換
                if sar[i] < high.iloc[i]:
                    direction[i] = "LONG"
                    sar[i] = ep[i - 1]  # 前回のEP（最安値）をSARとする
                    ep[i] = high.iloc[i]
                    af[i] = af_start
                else:
                    # トレンド継続
                    if low.iloc[i] < ep[i - 1]:
                        ep[i] = low.iloc[i]
                        af[i] = min(af[i - 1] + af_increment, af_max)

                    # SARは前2日の高値を超えないように調整
                    if i >= 2:
                        sar[i] = max(sar[i], high.iloc[i - 1], high.iloc[i - 2])
                    elif i >= 1:
                        sar[i] = max(sar[i], high.iloc[i - 1])

        return {
            "sar": pd.Series(sar, index=high.index),
            "direction": pd.Series(direction, index=high.index),
        }

    def _calculate_ichimoku(self, high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
        """一目均衡表計算"""
        # 転換線（9日）
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        # 基準線（26日）
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        # 先行スパンA（26日先行）
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        # 先行スパンB（26日先行）
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(
            26
        )
        # 遅行スパン（終値を26日過去にシフト）
        chikou_span = close.shift(-26)
        # 雲の厚さ
        kumo_thickness = abs(senkou_span_a - senkou_span_b)
        # 価格が雲の上か下か
        is_above_kumo = (close > senkou_span_a) & (close > senkou_span_b)
        is_below_kumo = (close < senkou_span_a) & (close < senkou_span_b)

        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_span_a,
            "senkou_span_b": senkou_span_b,
            "chikou_span": chikou_span,
            "kumo_thickness": kumo_thickness,
            "is_above_kumo": is_above_kumo,
            "is_below_kumo": is_below_kumo,
        }

    def _calculate_keltner_channel(
        self, close: pd.Series, high: pd.Series, low: pd.Series, period: int = 20
    ) -> dict:
        """ケルトナーチャネル計算"""
        middle = close.ewm(span=period, adjust=False).mean()
        atr = (
            pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1)
            .max(axis=1)
            .rolling(window=period)
            .mean()
        )
        upper = middle + 2 * atr
        lower = middle - 2 * atr
        return {"upper": upper, "middle": middle, "lower": lower}

    def _calculate_vwap(
        self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20
    ) -> pd.Series:
        """VWAP計算（20日ローリング版）

        日次データでは本来のVWAP（日中累積）を計算できないため、
        過去20日間の出来高加重平均価格として算出。
        ローリングウィンドウにより、全量計算と差分計算で冪等性を保証。
        """
        tp = (high + low + close) / 3
        return (tp * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()

    def _calculate_vwma(self, close: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        """出来高加重移動平均計算"""
        return (close * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()

    def _calculate_cmf(
        self, high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20
    ) -> pd.Series:
        """Chaikin Money Flow計算"""
        mfm = ((close - low) - (high - close)) / (high - low)
        mfv = mfm * volume
        return mfv.rolling(window=period).sum() / volume.rolling(window=period).sum()

    def _calculate_candlestick_patterns(
        self, open_price: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series
    ) -> dict:
        """ローソク足パターン計算"""
        body = abs(close - open_price)
        range_hl = high - low
        upper_shadow = high - pd.concat([open_price, close], axis=1).max(axis=1)
        lower_shadow = pd.concat([open_price, close], axis=1).min(axis=1) - low

        # 十字線（実体が小さい）
        is_doji = body / range_hl < 0.1

        # ハンマー（下ヒゲが長い）
        is_hammer = (lower_shadow > body * 2) & (upper_shadow < body * 0.5)

        # 逆ハンマー（上ヒゲが長い）
        is_inverted_hammer = (upper_shadow > body * 2) & (lower_shadow < body * 0.5)

        # 流れ星（上ヒゲが長く陰線）
        is_shooting_star = (upper_shadow > body * 2) & (close < open_price)

        # 首吊り線（下ヒゲが長く陰線）
        is_hanging_man = (lower_shadow > body * 2) & (close < open_price)

        # 連続陽線・陰線
        is_up = close > open_price
        is_down = close < open_price
        consecutive_up_days = is_up.astype(int).groupby((~is_up).cumsum()).cumsum()
        consecutive_down_days = is_down.astype(int).groupby((~is_down).cumsum()).cumsum()

        # 実体・ヒゲの比率
        body_size = body / range_hl
        upper_shadow_ratio = upper_shadow / range_hl
        lower_shadow_ratio = lower_shadow / range_hl

        return {
            "is_doji": is_doji,
            "is_hammer": is_hammer,
            "is_inverted_hammer": is_inverted_hammer,
            "is_shooting_star": is_shooting_star,
            "is_hanging_man": is_hanging_man,
            "consecutive_up_days": consecutive_up_days,
            "consecutive_down_days": consecutive_down_days,
            "body_size": body_size,
            "upper_shadow_ratio": upper_shadow_ratio,
            "lower_shadow_ratio": lower_shadow_ratio,
        }

    def _calculate_awesome_oscillator(self, high: pd.Series, low: pd.Series) -> pd.Series:
        """Awesome Oscillator計算"""
        median_price = (high + low) / 2
        ao = median_price.rolling(window=5).mean() - median_price.rolling(window=34).mean()
        return ao

    def _calculate_aroon(self, high: pd.Series, low: pd.Series, period: int = 25) -> dict:
        """Aroon Indicator計算

        Aroon Upは窓内の最高値からの経過日数が短いほど高くなる（最近最高値 = 強い上昇トレンド）
        Aroon Downは窓内の最安値からの経過日数が短いほど高くなる（最近最安値 = 強い下降トレンド）
        """
        # argmax/argminは0-indexed。最新日（右端）が最高値/最安値の場合、argmax/argmin = period-1
        # Aroon Up = ((期間 - 経過日数) / 期間) * 100 = ((argmax + 1) / 期間) * 100
        aroon_up = (
            high.rolling(window=period).apply(lambda x: x.argmax() + 1, raw=True) / period
        ) * 100
        aroon_down = (
            low.rolling(window=period).apply(lambda x: x.argmin() + 1, raw=True) / period
        ) * 100
        aroon_oscillator = aroon_up - aroon_down
        return {"up": aroon_up, "down": aroon_down, "oscillator": aroon_oscillator}

    def _calculate_gc_dc_days(self, ma_short: pd.Series, ma_long: pd.Series) -> dict:
        """ゴールデンクロス/デッドクロスからの経過日数計算

        Args:
            ma_short: 短期移動平均線
            ma_long: 長期移動平均線

        Returns:
            dict: ゴールデンクロス/デッドクロスからの経過日数
        """
        # 両MAが確定している区間のみでクロスを検出（未確定期間の誤検出を防止）
        # 例: MA200の場合、200日目までは未確定なのでNaNのまま維持
        valid = ma_short.notna() & ma_long.notna()
        cross = (ma_short > ma_long).where(valid).astype("Int64")

        # ゴールデンクロス: 0 → 1 への変化
        # デッドクロス: 1 → 0 への変化
        cross_diff = cross.diff()
        gc_occurred = (cross_diff == 1).fillna(False)
        dc_occurred = (cross_diff == -1).fillna(False)

        # ゴールデンクロスからの経過日数
        days_since_gc = pd.Series(index=ma_short.index, dtype=pd.Int64Dtype())
        days_since_dc = pd.Series(index=ma_short.index, dtype=pd.Int64Dtype())

        gc_day_counter = None
        dc_day_counter = None

        for i in range(len(cross)):
            if gc_occurred.iloc[i]:
                # ゴールデンクロス発生
                gc_day_counter = 0
                dc_day_counter = None
            elif dc_occurred.iloc[i]:
                # デッドクロス発生
                dc_day_counter = 0
                gc_day_counter = None
            else:
                # クロスなし: カウンタを進める
                if gc_day_counter is not None:
                    gc_day_counter += 1
                if dc_day_counter is not None:
                    dc_day_counter += 1

            # 結果に記録
            days_since_gc.iloc[i] = gc_day_counter
            days_since_dc.iloc[i] = dc_day_counter

        return {
            "days_since_gc": days_since_gc,
            "days_since_dc": days_since_dc,
        }
