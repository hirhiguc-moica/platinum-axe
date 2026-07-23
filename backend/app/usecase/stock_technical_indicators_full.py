"""テクニカル指標完全履歴取得ユースケース（全125指標）"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.technical_indicator_repository import (
    TechnicalIndicatorRepository,
)


class GetStockTechnicalIndicatorsFullUseCase:
    """テクニカル指標完全履歴取得ユースケース（全125指標、ページング対応）"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.technical_repo = TechnicalIndicatorRepository(session)

    async def execute(
        self,
        stock_code: str,
        page: int = 1,
        limit: int = 200,
    ) -> dict:
        """テクニカル指標完全履歴取得（全125指標）

        Args:
            stock_code: 銘柄コード
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数

        Returns:
            テクニカル指標完全履歴データ（ページング情報付き、全125指標）
        """
        offset = (page - 1) * limit

        # データ取得
        indicators = await self.technical_repo.find_by_stock_code(
            stock_code=stock_code,
            limit=limit,
            offset=offset,
        )

        # 総件数取得
        total = await self.technical_repo.count_by_stock_code(stock_code)

        # レスポンス整形（全指標を含む）
        items = []
        for ind in indicators:
            item = {
                "date": ind.date,
                # ==========================================
                # 1. 移動平均線
                # ==========================================
                "ma_5": float(ind.ma_5) if ind.ma_5 else None,
                "ma_10": float(ind.ma_10) if ind.ma_10 else None,
                "ma_25": float(ind.ma_25) if ind.ma_25 else None,
                "ma_50": float(ind.ma_50) if ind.ma_50 else None,
                "ma_75": float(ind.ma_75) if ind.ma_75 else None,
                "ma_100": float(ind.ma_100) if ind.ma_100 else None,
                "ma_200": float(ind.ma_200) if ind.ma_200 else None,
                "ema_5": float(ind.ema_5) if ind.ema_5 else None,
                "ema_12": float(ind.ema_12) if ind.ema_12 else None,
                "ema_26": float(ind.ema_26) if ind.ema_26 else None,
                "ema_50": float(ind.ema_50) if ind.ema_50 else None,
                "ema_200": float(ind.ema_200) if ind.ema_200 else None,
                "wma_20": float(ind.wma_20) if ind.wma_20 else None,
                # ==========================================
                # 2. 移動平均の派生特徴量
                # ==========================================
                "deviation_from_ma5": float(ind.deviation_from_ma5)
                if ind.deviation_from_ma5
                else None,
                "deviation_from_ma25": float(ind.deviation_from_ma25)
                if ind.deviation_from_ma25
                else None,
                "deviation_from_ma75": float(ind.deviation_from_ma75)
                if ind.deviation_from_ma75
                else None,
                "deviation_from_ma200": float(ind.deviation_from_ma200)
                if ind.deviation_from_ma200
                else None,
                "ma_5_25_deviation": float(ind.ma_5_25_deviation)
                if ind.ma_5_25_deviation
                else None,
                "ma_25_75_deviation": float(ind.ma_25_75_deviation)
                if ind.ma_25_75_deviation
                else None,
                "ma_75_200_deviation": float(ind.ma_75_200_deviation)
                if ind.ma_75_200_deviation
                else None,
                "ma_5_slope_5d": float(ind.ma_5_slope_5d) if ind.ma_5_slope_5d else None,
                "ma_25_slope_5d": float(ind.ma_25_slope_5d) if ind.ma_25_slope_5d else None,
                "ma_75_slope_10d": float(ind.ma_75_slope_10d) if ind.ma_75_slope_10d else None,
                "days_since_gc_5_25": ind.days_since_gc_5_25,
                "days_since_dc_5_25": ind.days_since_dc_5_25,
                "days_since_gc_25_75": ind.days_since_gc_25_75,
                "days_since_dc_25_75": ind.days_since_dc_25_75,
                "is_perfect_order_bullish": ind.is_perfect_order_bullish,
                "is_perfect_order_bearish": ind.is_perfect_order_bearish,
                # ==========================================
                # 3. 騰落率
                # ==========================================
                "return_1d": float(ind.return_1d) if ind.return_1d else None,
                "return_3d": float(ind.return_3d) if ind.return_3d else None,
                "return_5d": float(ind.return_5d) if ind.return_5d else None,
                "return_10d": float(ind.return_10d) if ind.return_10d else None,
                "return_20d": float(ind.return_20d) if ind.return_20d else None,
                "return_60d": float(ind.return_60d) if ind.return_60d else None,
                "return_120d": float(ind.return_120d) if ind.return_120d else None,
                "log_return_1d": float(ind.log_return_1d) if ind.log_return_1d else None,
                "log_return_5d": float(ind.log_return_5d) if ind.log_return_5d else None,
                "log_return_20d": float(ind.log_return_20d) if ind.log_return_20d else None,
                # ==========================================
                # 4. モメンタム系
                # ==========================================
                "rsi_9": float(ind.rsi_9) if ind.rsi_9 else None,
                "rsi_14": float(ind.rsi_14) if ind.rsi_14 else None,
                "rsi_25": float(ind.rsi_25) if ind.rsi_25 else None,
                "macd": float(ind.macd) if ind.macd else None,
                "macd_signal": float(ind.macd_signal) if ind.macd_signal else None,
                "macd_histogram": float(ind.macd_histogram) if ind.macd_histogram else None,
                "stochastic_k": float(ind.stochastic_k) if ind.stochastic_k else None,
                "stochastic_d": float(ind.stochastic_d) if ind.stochastic_d else None,
                "stochastic_slow_d": float(ind.stochastic_slow_d)
                if ind.stochastic_slow_d
                else None,
                "roc_12": float(ind.roc_12) if ind.roc_12 else None,
                "roc_25": float(ind.roc_25) if ind.roc_25 else None,
                "momentum_10": float(ind.momentum_10) if ind.momentum_10 else None,
                "momentum_20": float(ind.momentum_20) if ind.momentum_20 else None,
                "cci_14": float(ind.cci_14) if ind.cci_14 else None,
                "cci_20": float(ind.cci_20) if ind.cci_20 else None,
                "williams_r_14": float(ind.williams_r_14) if ind.williams_r_14 else None,
                "mfi_14": float(ind.mfi_14) if ind.mfi_14 else None,
                "ultimate_oscillator": float(ind.ultimate_oscillator)
                if ind.ultimate_oscillator
                else None,
                # ==========================================
                # 5. トレンド指標
                # ==========================================
                "adx_14": float(ind.adx_14) if ind.adx_14 else None,
                "plus_di_14": float(ind.plus_di_14) if ind.plus_di_14 else None,
                "minus_di_14": float(ind.minus_di_14) if ind.minus_di_14 else None,
                "parabolic_sar": float(ind.parabolic_sar) if ind.parabolic_sar else None,
                "sar_direction": ind.sar_direction,
                "tenkan_sen": float(ind.tenkan_sen) if ind.tenkan_sen else None,
                "kijun_sen": float(ind.kijun_sen) if ind.kijun_sen else None,
                "senkou_span_a": float(ind.senkou_span_a) if ind.senkou_span_a else None,
                "senkou_span_b": float(ind.senkou_span_b) if ind.senkou_span_b else None,
                "chikou_span": float(ind.chikou_span) if ind.chikou_span else None,
                "kumo_thickness": float(ind.kumo_thickness) if ind.kumo_thickness else None,
                "is_above_kumo": ind.is_above_kumo,
                "is_below_kumo": ind.is_below_kumo,
                # ==========================================
                # 6. ボラティリティ指標
                # ==========================================
                "bollinger_upper_2sigma": float(ind.bollinger_upper_2sigma)
                if ind.bollinger_upper_2sigma
                else None,
                "bollinger_middle": float(ind.bollinger_middle) if ind.bollinger_middle else None,
                "bollinger_lower_2sigma": float(ind.bollinger_lower_2sigma)
                if ind.bollinger_lower_2sigma
                else None,
                "bollinger_width": float(ind.bollinger_width) if ind.bollinger_width else None,
                "bollinger_position": float(ind.bollinger_position)
                if ind.bollinger_position
                else None,
                "atr_14": float(ind.atr_14) if ind.atr_14 else None,
                "atr_20": float(ind.atr_20) if ind.atr_20 else None,
                "volatility_10d": float(ind.volatility_10d) if ind.volatility_10d else None,
                "volatility_20d": float(ind.volatility_20d) if ind.volatility_20d else None,
                "volatility_60d": float(ind.volatility_60d) if ind.volatility_60d else None,
                "keltner_upper": float(ind.keltner_upper) if ind.keltner_upper else None,
                "keltner_middle": float(ind.keltner_middle) if ind.keltner_middle else None,
                "keltner_lower": float(ind.keltner_lower) if ind.keltner_lower else None,
                # ==========================================
                # 7. 出来高系
                # ==========================================
                "volume_ma_5": ind.volume_ma_5,
                "volume_ma_10": ind.volume_ma_10,
                "volume_ma_20": ind.volume_ma_20,
                "volume_ma_60": ind.volume_ma_60,
                "volume_ratio_5": float(ind.volume_ratio_5) if ind.volume_ratio_5 else None,
                "volume_ratio_20": float(ind.volume_ratio_20) if ind.volume_ratio_20 else None,
                "volume_change_1d": float(ind.volume_change_1d) if ind.volume_change_1d else None,
                "volume_change_5d": float(ind.volume_change_5d) if ind.volume_change_5d else None,
                "obv": ind.obv,
                "obv_ma_20": ind.obv_ma_20,
                "vwap": float(ind.vwap) if ind.vwap else None,
                "vwma_20": float(ind.vwma_20) if ind.vwma_20 else None,
                "cmf_20": float(ind.cmf_20) if ind.cmf_20 else None,
                # ==========================================
                # 8. 価格位置・高値安値
                # ==========================================
                "high_5d": float(ind.high_5d) if ind.high_5d else None,
                "low_5d": float(ind.low_5d) if ind.low_5d else None,
                "high_20d": float(ind.high_20d) if ind.high_20d else None,
                "low_20d": float(ind.low_20d) if ind.low_20d else None,
                "high_60d": float(ind.high_60d) if ind.high_60d else None,
                "low_60d": float(ind.low_60d) if ind.low_60d else None,
                "high_52w": float(ind.high_52w) if ind.high_52w else None,
                "low_52w": float(ind.low_52w) if ind.low_52w else None,
                "price_from_high_5d": float(ind.price_from_high_5d)
                if ind.price_from_high_5d
                else None,
                "price_from_low_5d": float(ind.price_from_low_5d)
                if ind.price_from_low_5d
                else None,
                "price_from_high_20d": float(ind.price_from_high_20d)
                if ind.price_from_high_20d
                else None,
                "price_from_low_20d": float(ind.price_from_low_20d)
                if ind.price_from_low_20d
                else None,
                "price_from_high_52w": float(ind.price_from_high_52w)
                if ind.price_from_high_52w
                else None,
                "price_from_low_52w": float(ind.price_from_low_52w)
                if ind.price_from_low_52w
                else None,
                "price_position_20d": float(ind.price_position_20d)
                if ind.price_position_20d
                else None,
                "price_position_52w": float(ind.price_position_52w)
                if ind.price_position_52w
                else None,
                "is_new_high_20d": ind.is_new_high_20d,
                "is_new_low_20d": ind.is_new_low_20d,
                "is_new_high_52w": ind.is_new_high_52w,
                "is_new_low_52w": ind.is_new_low_52w,
                # ==========================================
                # 9. ローソク足パターン
                # ==========================================
                "is_doji": ind.is_doji,
                "is_hammer": ind.is_hammer,
                "is_inverted_hammer": ind.is_inverted_hammer,
                "is_shooting_star": ind.is_shooting_star,
                "is_hanging_man": ind.is_hanging_man,
                "consecutive_up_days": ind.consecutive_up_days,
                "consecutive_down_days": ind.consecutive_down_days,
                "body_size": float(ind.body_size) if ind.body_size else None,
                "upper_shadow_ratio": float(ind.upper_shadow_ratio)
                if ind.upper_shadow_ratio
                else None,
                "lower_shadow_ratio": float(ind.lower_shadow_ratio)
                if ind.lower_shadow_ratio
                else None,
                # ==========================================
                # 10. その他の指標
                # ==========================================
                "awesome_oscillator": float(ind.awesome_oscillator)
                if ind.awesome_oscillator
                else None,
                "aroon_up": float(ind.aroon_up) if ind.aroon_up else None,
                "aroon_down": float(ind.aroon_down) if ind.aroon_down else None,
                "aroon_oscillator": float(ind.aroon_oscillator) if ind.aroon_oscillator else None,
            }
            items.append(item)

        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        }
