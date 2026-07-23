"""テクニカル指標関連モデル"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class TechnicalIndicator(TimestampMixin, Base):
    """テクニカル指標"""

    __tablename__ = "technical_indicators"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="日付")

    # ==========================================
    # 1. 移動平均線
    # ==========================================
    # 単純移動平均（SMA）
    ma_5: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="5日移動平均")
    ma_10: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="10日移動平均")
    ma_25: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="25日移動平均")
    ma_50: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="50日移動平均")
    ma_75: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="75日移動平均")
    ma_100: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="100日移動平均")
    ma_200: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="200日移動平均")

    # 指数移動平均（EMA）
    ema_5: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="5日指数移動平均")
    ema_12: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="12日指数移動平均")
    ema_26: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="26日指数移動平均")
    ema_50: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="50日指数移動平均")
    ema_200: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="200日指数移動平均")

    # 加重移動平均（WMA）
    wma_20: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="20日加重移動平均")

    # ==========================================
    # 2. 移動平均の派生特徴量
    # ==========================================
    # 乖離率（Deviation）
    deviation_from_ma5: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA5からの乖離率"
    )
    deviation_from_ma25: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA25からの乖離率"
    )
    deviation_from_ma75: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA75からの乖離率"
    )
    deviation_from_ma200: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA200からの乖離率"
    )

    # 移動平均間の乖離率
    ma_5_25_deviation: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA5-MA25乖離率"
    )
    ma_25_75_deviation: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA25-MA75乖離率"
    )
    ma_75_200_deviation: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="MA75-MA200乖離率"
    )

    # 移動平均の傾き（Slope）
    ma_5_slope_5d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="MA5の5日傾き")
    ma_25_slope_5d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="MA25の5日傾き")
    ma_75_slope_10d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="MA75の10日傾き")

    # ゴールデンクロス/デッドクロスからの経過日数
    days_since_gc_5_25: Mapped[int | None] = mapped_column(Integer, comment="MA5×MA25 GCからの日数")
    days_since_dc_5_25: Mapped[int | None] = mapped_column(Integer, comment="MA5×MA25 DCからの日数")
    days_since_gc_25_75: Mapped[int | None] = mapped_column(
        Integer, comment="MA25×MA75 GCからの日数"
    )
    days_since_dc_25_75: Mapped[int | None] = mapped_column(
        Integer, comment="MA25×MA75 DCからの日数"
    )

    # 移動平均の並び順（パーフェクトオーダー判定）
    is_perfect_order_bullish: Mapped[bool | None] = mapped_column(
        Boolean, comment="パーフェクトオーダー（買い）"
    )
    is_perfect_order_bearish: Mapped[bool | None] = mapped_column(
        Boolean, comment="パーフェクトオーダー（売り）"
    )

    # ==========================================
    # 3. 騰落率（Return）
    # ==========================================
    return_1d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="1日騰落率")
    return_3d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="3日騰落率")
    return_5d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="5日騰落率")
    return_10d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="10日騰落率")
    return_20d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="20日騰落率")
    return_60d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="60日騰落率")
    return_120d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="120日騰落率")

    # 対数収益率（Log Return）
    log_return_1d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="1日対数収益率")
    log_return_5d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="5日対数収益率")
    log_return_20d: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="20日対数収益率")

    # ==========================================
    # 4. モメンタム系
    # ==========================================
    # RSI（Relative Strength Index）
    rsi_9: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="RSI(9日)")
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="RSI(14日)")
    rsi_25: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="RSI(25日)")

    # MACD
    macd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="MACD")
    macd_signal: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="MACDシグナル")
    macd_histogram: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="MACDヒストグラム"
    )

    # ストキャスティクス
    stochastic_k: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="%K")
    stochastic_d: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="%D")
    stochastic_slow_d: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="Slow %D")

    # ROC（Rate of Change）
    roc_12: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="12日ROC")
    roc_25: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="25日ROC")

    # モメンタム
    momentum_10: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="10日モメンタム")
    momentum_20: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="20日モメンタム")

    # CCI（Commodity Channel Index）
    cci_14: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), comment="14日CCI")
    cci_20: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), comment="20日CCI")

    # ウィリアムズ%R
    williams_r_14: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="14日ウィリアムズ%R"
    )

    # MFI（Money Flow Index）
    mfi_14: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="14日MFI")

    # Ultimate Oscillator
    ultimate_oscillator: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="Ultimate Oscillator"
    )

    # ==========================================
    # 5. トレンド指標
    # ==========================================
    # ADX（Average Directional Index）
    adx_14: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="14日ADX")
    plus_di_14: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="+DI(14日)")
    minus_di_14: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="-DI(14日)")

    # パラボリックSAR
    parabolic_sar: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="パラボリックSAR値"
    )
    sar_direction: Mapped[str | None] = mapped_column(String(10), comment="SAR方向（LONG/SHORT）")

    # 一目均衡表（Ichimoku）
    tenkan_sen: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="転換線（9日）")
    kijun_sen: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="基準線（26日）")
    senkou_span_a: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="先行スパンA")
    senkou_span_b: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="先行スパンB")
    chikou_span: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="遅行スパン")

    # 雲の厚さ
    kumo_thickness: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="雲の厚さ")
    is_above_kumo: Mapped[bool | None] = mapped_column(Boolean, comment="価格が雲の上")
    is_below_kumo: Mapped[bool | None] = mapped_column(Boolean, comment="価格が雲の下")

    # ==========================================
    # 6. ボラティリティ指標
    # ==========================================
    # ボリンジャーバンド
    bollinger_upper_2sigma: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="ボリンジャー上限2σ"
    )
    bollinger_middle: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="ボリンジャー中心線"
    )
    bollinger_lower_2sigma: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="ボリンジャー下限2σ"
    )
    bollinger_width: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="ボリンジャーバンド幅"
    )
    bollinger_position: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="バンド内位置（%B）"
    )

    # ATR（Average True Range）
    atr_14: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="14日ATR")
    atr_20: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="20日ATR")

    # ヒストリカル・ボラティリティ
    volatility_10d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="10日ボラティリティ"
    )
    volatility_20d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="20日ボラティリティ"
    )
    volatility_60d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="60日ボラティリティ"
    )

    # ケルトナーチャネル
    keltner_upper: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="ケルトナー上限")
    keltner_middle: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="ケルトナー中心")
    keltner_lower: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="ケルトナー下限")

    # ==========================================
    # 7. 出来高系
    # ==========================================
    # 出来高移動平均
    volume_ma_5: Mapped[int | None] = mapped_column(comment="5日平均出来高")
    volume_ma_10: Mapped[int | None] = mapped_column(comment="10日平均出来高")
    volume_ma_20: Mapped[int | None] = mapped_column(comment="20日平均出来高")
    volume_ma_60: Mapped[int | None] = mapped_column(comment="60日平均出来高")

    # 出来高比率
    volume_ratio_5: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="出来高比率（5日）"
    )
    volume_ratio_20: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="出来高比率（20日）"
    )

    # 出来高変化率
    volume_change_1d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="1日出来高変化率"
    )
    volume_change_5d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="5日出来高変化率"
    )

    # OBV（On-Balance Volume）
    obv: Mapped[int | None] = mapped_column(comment="OBV")
    obv_ma_20: Mapped[int | None] = mapped_column(comment="20日OBV移動平均")

    # VWAP（Volume Weighted Average Price）
    vwap: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="VWAP")

    # 出来高加重移動平均
    vwma_20: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="20日出来高加重移動平均"
    )

    # CMF（Chaikin Money Flow）
    cmf_20: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="20日CMF")

    # ==========================================
    # 8. 価格位置・高値安値
    # ==========================================
    # 高値・安値
    high_5d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="5日高値")
    low_5d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="5日安値")
    high_20d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="20日高値")
    low_20d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="20日安値")
    high_60d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="60日高値")
    low_60d: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="60日安値")
    high_52w: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="52週高値")
    low_52w: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="52週安値")

    # 高値・安値からの乖離率
    price_from_high_5d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="5日高値からの乖離率"
    )
    price_from_low_5d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="5日安値からの乖離率"
    )
    price_from_high_20d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="20日高値からの乖離率"
    )
    price_from_low_20d: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="20日安値からの乖離率"
    )
    price_from_high_52w: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="52週高値からの乖離率"
    )
    price_from_low_52w: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="52週安値からの乖離率"
    )

    # 価格の相対位置
    price_position_20d: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), comment="20日価格相対位置"
    )
    price_position_52w: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), comment="52週価格相対位置"
    )

    # 新高値・新安値判定
    is_new_high_20d: Mapped[bool | None] = mapped_column(Boolean, comment="20日新高値")
    is_new_low_20d: Mapped[bool | None] = mapped_column(Boolean, comment="20日新安値")
    is_new_high_52w: Mapped[bool | None] = mapped_column(Boolean, comment="52週新高値")
    is_new_low_52w: Mapped[bool | None] = mapped_column(Boolean, comment="52週新安値")

    # ==========================================
    # 9. ローソク足パターン
    # ==========================================
    # 基本パターン
    is_doji: Mapped[bool | None] = mapped_column(Boolean, comment="十字線")
    is_hammer: Mapped[bool | None] = mapped_column(Boolean, comment="ハンマー")
    is_inverted_hammer: Mapped[bool | None] = mapped_column(Boolean, comment="逆ハンマー")
    is_shooting_star: Mapped[bool | None] = mapped_column(Boolean, comment="流れ星")
    is_hanging_man: Mapped[bool | None] = mapped_column(Boolean, comment="首吊り線")

    # 連続パターン
    consecutive_up_days: Mapped[int | None] = mapped_column(Integer, comment="連続陽線日数")
    consecutive_down_days: Mapped[int | None] = mapped_column(Integer, comment="連続陰線日数")

    # 実体・ヒゲの比率
    body_size: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="実体サイズ")
    upper_shadow_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="上ヒゲ比率")
    lower_shadow_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), comment="下ヒゲ比率")

    # ==========================================
    # 10. その他の指標
    # ==========================================
    # Awesome Oscillator
    awesome_oscillator: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="Awesome Oscillator"
    )

    # Aroon Indicator
    aroon_up: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="Aroon Up")
    aroon_down: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), comment="Aroon Down")
    aroon_oscillator: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), comment="Aroon Oscillator"
    )

    # ==========================================
    # メタ情報
    # ==========================================
    calculated_at: Mapped[date] = mapped_column(Date, nullable=False, comment="計算日時")

    __table_args__ = (
        Index(
            "idx_technical_indicators_code_date",
            "stock_code",
            "date",
            postgresql_using="btree",
        ),
        Index("idx_technical_indicators_date", "date", postgresql_using="btree"),
        {"comment": "テクニカル指標"},
    )

    def __repr__(self) -> str:
        return (
            f"<TechnicalIndicator(code={self.stock_code}, date={self.date}, rsi_14={self.rsi_14})>"
        )
