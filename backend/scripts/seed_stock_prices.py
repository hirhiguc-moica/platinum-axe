"""株価モックデータ生成スクリプト

トヨタ自動車（7203）の1年分（約240営業日）の株価データと
125項目のテクニカル指標を生成してDBに保存する。
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

# プロジェクトルートをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import StockMaster, StockPriceDaily, TechnicalIndicator
from app.infrastructure.database import AsyncSessionLocal


def generate_realistic_ohlc(
    days: int = 240,
    initial_price: float = 2500.0,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """リアルな株価四本値を生成

    Args:
        days: 営業日数
        initial_price: 初期株価
        volatility: ボラティリティ（日次変動率）

    Returns:
        pd.DataFrame: 株価データ（date, open, high, low, close, volume）
    """
    np.random.seed(42)  # 再現性のため

    # 日付生成（土日を除外）
    dates = []
    current = date.today() - timedelta(days=days)
    while len(dates) < days:
        if current.weekday() < 5:  # 月〜金のみ
            dates.append(current)
        current += timedelta(days=1)

    # 終値生成（幾何ブラウン運動）
    returns = np.random.normal(0.0002, volatility, days)  # わずかな上昇トレンド
    price_multipliers = np.exp(returns)
    closes = initial_price * np.cumprod(price_multipliers)

    # OHLC生成
    data = []
    for i, (dt, close) in enumerate(zip(dates, closes)):
        # 前日終値を基準に当日の値動きを生成
        prev_close = closes[i - 1] if i > 0 else initial_price

        # 寄り付きは前日終値付近でギャップを持つ場合あり
        gap = np.random.normal(0, volatility * 0.3)
        open_price = prev_close * (1 + gap)

        # 高値・安値はcloseとopenを超えない範囲で生成
        intraday_range = abs(close - open_price) * np.random.uniform(1.2, 2.0)
        high_price = max(open_price, close) + abs(np.random.normal(0, intraday_range * 0.3))
        low_price = min(open_price, close) - abs(np.random.normal(0, intraday_range * 0.3))

        # 出来高（10,000,000〜30,000,000株程度）
        base_volume = 15_000_000
        volume_variation = np.random.uniform(0.5, 2.0)
        volume = int(base_volume * volume_variation)

        # 売買代金
        turnover = volume * close

        data.append({
            "date": dt,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close, 2),
            "volume": volume,
            "turnover_value": round(turnover, 2),
        })

    df = pd.DataFrame(data)

    # 調整係数（今回は分割・配当なしと仮定）
    df["adjustment_factor"] = 1.0
    df["adjusted_open"] = df["open"]
    df["adjusted_high"] = df["high"]
    df["adjusted_low"] = df["low"]
    df["adjusted_close"] = df["close"]
    df["adjusted_volume"] = df["volume"]

    return df


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """125項目のテクニカル指標を計算

    Args:
        df: 株価データ（date, open, high, low, close, volume）

    Returns:
        pd.DataFrame: テクニカル指標データ
    """
    result = pd.DataFrame()
    result["date"] = df["date"]

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # ==========================================
    # 1. 移動平均線（13種）
    # ==========================================
    result["ma_5"] = close.rolling(5).mean()
    result["ma_10"] = close.rolling(10).mean()
    result["ma_25"] = close.rolling(25).mean()
    result["ma_50"] = close.rolling(50).mean()
    result["ma_75"] = close.rolling(75).mean()
    result["ma_100"] = close.rolling(100).mean()
    result["ma_200"] = close.rolling(200).mean()

    result["ema_5"] = close.ewm(span=5, adjust=False).mean()
    result["ema_12"] = close.ewm(span=12, adjust=False).mean()
    result["ema_26"] = close.ewm(span=26, adjust=False).mean()
    result["ema_50"] = close.ewm(span=50, adjust=False).mean()
    result["ema_200"] = close.ewm(span=200, adjust=False).mean()

    result["wma_20"] = close.rolling(20).apply(
        lambda x: (x * np.arange(1, len(x) + 1)).sum() / np.arange(1, len(x) + 1).sum(),
        raw=True
    )

    # ==========================================
    # 2. 移動平均派生特徴量（14種）
    # ==========================================
    result["deviation_from_ma5"] = (close - result["ma_5"]) / result["ma_5"]
    result["deviation_from_ma25"] = (close - result["ma_25"]) / result["ma_25"]
    result["deviation_from_ma75"] = (close - result["ma_75"]) / result["ma_75"]
    result["deviation_from_ma200"] = (close - result["ma_200"]) / result["ma_200"]

    result["ma_5_25_deviation"] = (result["ma_5"] - result["ma_25"]) / result["ma_25"]
    result["ma_25_75_deviation"] = (result["ma_25"] - result["ma_75"]) / result["ma_75"]
    result["ma_75_200_deviation"] = (result["ma_75"] - result["ma_200"]) / result["ma_200"]

    # 傾き（5日間の変化率）
    result["ma_5_slope_5d"] = result["ma_5"].pct_change(5)
    result["ma_25_slope_5d"] = result["ma_25"].pct_change(5)
    result["ma_75_slope_10d"] = result["ma_75"].pct_change(10)

    # GC/DCからの経過日数（簡易版: クロス検出）
    gc_5_25 = (result["ma_5"] > result["ma_25"]) & (result["ma_5"].shift(1) <= result["ma_25"].shift(1))
    dc_5_25 = (result["ma_5"] < result["ma_25"]) & (result["ma_5"].shift(1) >= result["ma_25"].shift(1))
    gc_25_75 = (result["ma_25"] > result["ma_75"]) & (result["ma_25"].shift(1) <= result["ma_75"].shift(1))
    dc_25_75 = (result["ma_25"] < result["ma_75"]) & (result["ma_25"].shift(1) >= result["ma_75"].shift(1))

    result["days_since_gc_5_25"] = None
    result["days_since_dc_5_25"] = None
    result["days_since_gc_25_75"] = None
    result["days_since_dc_25_75"] = None

    # パーフェクトオーダー
    result["is_perfect_order_bullish"] = (
        (result["ma_5"] > result["ma_25"]) &
        (result["ma_25"] > result["ma_75"]) &
        (result["ma_75"] > result["ma_200"])
    ).astype(int)
    result["is_perfect_order_bearish"] = (
        (result["ma_5"] < result["ma_25"]) &
        (result["ma_25"] < result["ma_75"]) &
        (result["ma_75"] < result["ma_200"])
    ).astype(int)

    # ==========================================
    # 3. 騰落率（10種）
    # ==========================================
    result["return_1d"] = close.pct_change(1)
    result["return_3d"] = close.pct_change(3)
    result["return_5d"] = close.pct_change(5)
    result["return_10d"] = close.pct_change(10)
    result["return_20d"] = close.pct_change(20)
    result["return_60d"] = close.pct_change(60)
    result["return_120d"] = close.pct_change(120)

    result["log_return_1d"] = np.log(close / close.shift(1))
    result["log_return_5d"] = np.log(close / close.shift(5))
    result["log_return_20d"] = np.log(close / close.shift(20))

    # ==========================================
    # 4. モメンタム系（16種）
    # ==========================================
    # RSI
    for period in [9, 14, 25]:
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        result[f"rsi_{period}"] = 100 - (100 / (1 + rs))

    # MACD
    result["macd"] = result["ema_12"] - result["ema_26"]
    result["macd_signal"] = result["macd"].ewm(span=9, adjust=False).mean()
    result["macd_histogram"] = result["macd"] - result["macd_signal"]

    # Stochastic
    low_14 = low.rolling(14).min()
    high_14 = high.rolling(14).max()
    result["stochastic_k"] = 100 * (close - low_14) / (high_14 - low_14)
    result["stochastic_d"] = result["stochastic_k"].rolling(3).mean()
    result["stochastic_slow_d"] = result["stochastic_d"].rolling(3).mean()

    # CCI
    tp = (high + low + close) / 3
    result["cci_14"] = (tp - tp.rolling(14).mean()) / (0.015 * tp.rolling(14).std())
    result["cci_20"] = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std())

    # MFI (Money Flow Index)
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(14).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(14).sum()
    mfi_ratio = positive_flow / negative_flow
    result["mfi_14"] = 100 - (100 / (1 + mfi_ratio))

    # Williams %R
    result["williams_r_14"] = -100 * (high_14 - close) / (high_14 - low_14)

    # ROC (Rate of Change)
    result["roc_12"] = ((close - close.shift(12)) / close.shift(12)) * 100
    result["roc_25"] = ((close - close.shift(25)) / close.shift(25)) * 100

    # Momentum
    result["momentum_10"] = close - close.shift(10)
    result["momentum_20"] = close - close.shift(20)

    # ==========================================
    # 5. トレンド指標（13種）
    # ==========================================
    # ADX (簡易版)
    high_diff = high.diff()
    low_diff = -low.diff()

    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr_14 = tr.rolling(14).mean()

    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    result["adx_14"] = dx.rolling(14).mean()
    result["plus_di_14"] = plus_di
    result["minus_di_14"] = minus_di

    # Parabolic SAR (簡易版: EMAで代用)
    result["parabolic_sar"] = close.ewm(span=20, adjust=False).mean()
    # SAR方向（LONG/SHORT）
    result["sar_direction"] = (close > result["parabolic_sar"]).apply(lambda x: "LONG" if x else "SHORT")

    # 一目均衡表
    high_9_ichi = high.rolling(9).max()
    low_9_ichi = low.rolling(9).min()
    result["tenkan_sen"] = (high_9_ichi + low_9_ichi) / 2

    high_26 = high.rolling(26).max()
    low_26 = low.rolling(26).min()
    result["kijun_sen"] = (high_26 + low_26) / 2

    result["senkou_span_a"] = ((result["tenkan_sen"] + result["kijun_sen"]) / 2).shift(26)

    high_52 = high.rolling(52).max()
    low_52 = low.rolling(52).min()
    result["senkou_span_b"] = ((high_52 + low_52) / 2).shift(26)

    result["chikou_span"] = close.shift(-26)

    # 雲の厚さ
    result["kumo_thickness"] = (result["senkou_span_a"] - result["senkou_span_b"]).abs()

    # 雲との位置関係
    kumo_top = pd.concat([result["senkou_span_a"], result["senkou_span_b"]], axis=1).max(axis=1)
    kumo_bottom = pd.concat([result["senkou_span_a"], result["senkou_span_b"]], axis=1).min(axis=1)
    result["is_above_kumo"] = (close > kumo_top).astype(int)
    result["is_below_kumo"] = (close < kumo_bottom).astype(int)

    # Aroon
    result["aroon_up"] = 100 * close.rolling(25).apply(lambda x: x.argmax()) / 25
    result["aroon_down"] = 100 * close.rolling(25).apply(lambda x: x.argmin()) / 25
    result["aroon_oscillator"] = result["aroon_up"] - result["aroon_down"]

    # ==========================================
    # 6. ボラティリティ指標（12種）
    # ==========================================
    # ボリンジャーバンド
    bb_ma = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    result["bollinger_upper_2sigma"] = bb_ma + 2 * bb_std
    result["bollinger_middle"] = bb_ma
    result["bollinger_lower_2sigma"] = bb_ma - 2 * bb_std
    result["bollinger_width"] = (result["bollinger_upper_2sigma"] - result["bollinger_lower_2sigma"]) / result["bollinger_middle"]
    result["bollinger_position"] = (close - result["bollinger_lower_2sigma"]) / (result["bollinger_upper_2sigma"] - result["bollinger_lower_2sigma"])

    # ATR
    result["atr_14"] = atr_14
    result["atr_20"] = tr.rolling(20).mean()

    # ヒストリカル・ボラティリティ
    result["volatility_10d"] = close.pct_change().rolling(10).std() * np.sqrt(252)
    result["volatility_20d"] = close.pct_change().rolling(20).std() * np.sqrt(252)
    result["volatility_60d"] = close.pct_change().rolling(60).std() * np.sqrt(252)

    # Keltner Channel
    keltner_ma = close.ewm(span=20, adjust=False).mean()
    result["keltner_upper"] = keltner_ma + 2 * atr_14
    result["keltner_middle"] = keltner_ma
    result["keltner_lower"] = keltner_ma - 2 * atr_14

    # ==========================================
    # 7. 出来高系（13種）
    # ==========================================
    result["volume_ma_5"] = volume.rolling(5).mean()
    result["volume_ma_10"] = volume.rolling(10).mean()
    result["volume_ma_20"] = volume.rolling(20).mean()
    result["volume_ma_60"] = volume.rolling(60).mean()

    result["volume_ratio_5"] = volume / result["volume_ma_5"]
    result["volume_ratio_20"] = volume / result["volume_ma_20"]

    # OBV (On-Balance Volume)
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    result["obv"] = obv
    result["obv_ma_20"] = obv.rolling(20).mean()

    # VWAP (簡易版: 日次では意味薄いが計算)
    result["vwap"] = (close * volume).rolling(20).sum() / volume.rolling(20).sum()

    # VWMA (Volume Weighted Moving Average)
    result["vwma_20"] = (close * volume).rolling(20).sum() / volume.rolling(20).sum()

    # CMF (Chaikin Money Flow)
    mf_multiplier = ((close - low) - (high - close)) / (high - low)
    mf_volume = mf_multiplier * volume
    result["cmf_20"] = mf_volume.rolling(20).sum() / volume.rolling(20).sum()

    # Volume Change
    result["volume_change_1d"] = volume.pct_change(1)
    result["volume_change_5d"] = volume.pct_change(5)

    # ==========================================
    # 8. 価格位置・高値安値（19種）
    # ==========================================
    result["high_5d"] = high.rolling(5).max()
    result["low_5d"] = low.rolling(5).min()
    result["high_20d"] = high.rolling(20).max()
    result["low_20d"] = low.rolling(20).min()
    result["high_60d"] = high.rolling(60).max()
    result["low_60d"] = low.rolling(60).min()
    result["high_52w"] = high.rolling(252).max()
    result["low_52w"] = low.rolling(252).min()

    result["price_from_high_5d"] = (result["high_5d"] - close) / result["high_5d"]
    result["price_from_low_5d"] = (close - result["low_5d"]) / result["low_5d"]
    result["price_from_high_20d"] = (result["high_20d"] - close) / result["high_20d"]
    result["price_from_low_20d"] = (close - result["low_20d"]) / result["low_20d"]
    result["price_from_high_52w"] = (result["high_52w"] - close) / result["high_52w"]
    result["price_from_low_52w"] = (close - result["low_52w"]) / result["low_52w"]

    result["is_new_high_20d"] = (close == result["high_20d"]).astype(int)
    result["is_new_low_20d"] = (close == result["low_20d"]).astype(int)
    result["is_new_high_52w"] = (close == result["high_52w"]).astype(int)
    result["is_new_low_52w"] = (close == result["low_52w"]).astype(int)

    # レンジ内の位置
    result["price_position_20d"] = (close - result["low_20d"]) / (result["high_20d"] - result["low_20d"])
    result["price_position_52w"] = (close - result["low_52w"]) / (result["high_52w"] - result["low_52w"])

    # ==========================================
    # 9. ローソク足パターン（10種）
    # ==========================================
    body = close - df["open"]
    body_abs = body.abs()
    upper_shadow = high - pd.concat([close, df["open"]], axis=1).max(axis=1)
    lower_shadow = pd.concat([close, df["open"]], axis=1).min(axis=1) - low
    candle_range = high - low

    result["body_size"] = body_abs / df["open"]
    result["upper_shadow_ratio"] = upper_shadow / candle_range
    result["lower_shadow_ratio"] = lower_shadow / candle_range

    # Doji（十字線）
    result["is_doji"] = (body_abs / candle_range < 0.1).astype(int)

    # Hammer（ハンマー）
    result["is_hammer"] = (
        (lower_shadow > 2 * body_abs) &
        (upper_shadow < body_abs) &
        (body > 0)  # 陽線
    ).astype(int)

    # Hanging Man（首吊り線）
    result["is_hanging_man"] = (
        (lower_shadow > 2 * body_abs) &
        (upper_shadow < body_abs) &
        (body < 0)  # 陰線
    ).astype(int)

    # Inverted Hammer（逆ハンマー）
    result["is_inverted_hammer"] = (
        (upper_shadow > 2 * body_abs) &
        (lower_shadow < body_abs) &
        (body > 0)  # 陽線
    ).astype(int)

    # Shooting Star（流れ星）
    result["is_shooting_star"] = (
        (upper_shadow > 2 * body_abs) &
        (lower_shadow < body_abs) &
        (body < 0)  # 陰線
    ).astype(int)

    # Consecutive up/down days
    is_up = (close > close.shift(1)).astype(int)
    result["consecutive_up_days"] = is_up.groupby((is_up != is_up.shift()).cumsum()).cumsum()

    is_down = (close < close.shift(1)).astype(int)
    result["consecutive_down_days"] = is_down.groupby((is_down != is_down.shift()).cumsum()).cumsum()

    # ==========================================
    # 10. その他（5種）
    # ==========================================
    # Awesome Oscillator
    median_price = (high + low) / 2
    result["awesome_oscillator"] = median_price.rolling(5).mean() - median_price.rolling(34).mean()

    # Ultimate Oscillator (簡易版)
    bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
    tr_uo = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    avg7 = bp.rolling(7).sum() / tr_uo.rolling(7).sum()
    avg14 = bp.rolling(14).sum() / tr_uo.rolling(14).sum()
    avg28 = bp.rolling(28).sum() / tr_uo.rolling(28).sum()
    result["ultimate_oscillator"] = 100 * ((4 * avg7 + 2 * avg14 + avg28) / 7)

    return result


async def seed_stock_prices():
    """株価とテクニカル指標のモックデータを生成・投入"""

    stock_code = "7203"  # トヨタ自動車

    print(f"\n{'='*60}")
    print(f"株価モックデータ生成開始")
    print(f"銘柄: {stock_code} (トヨタ自動車)")
    print(f"{'='*60}\n")

    # 1. 株価データ生成
    print("⏳ 株価データ生成中...")
    df_prices = generate_realistic_ohlc(days=240, initial_price=2500.0)
    print(f"✅ {len(df_prices)}日分の株価データを生成しました")

    # 2. テクニカル指標計算
    print("\n⏳ テクニカル指標計算中（125項目）...")
    df_technical = calculate_technical_indicators(df_prices)
    print(f"✅ テクニカル指標を計算しました")

    # 3. DBに保存
    async with AsyncSessionLocal() as session:
        # 既存データ削除
        await session.execute(
            select(StockPriceDaily).where(StockPriceDaily.stock_code == stock_code)
        )
        existing_prices = (await session.execute(
            select(StockPriceDaily).where(StockPriceDaily.stock_code == stock_code)
        )).scalars().all()

        for price in existing_prices:
            await session.delete(price)

        await session.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.stock_code == stock_code)
        )
        existing_indicators = (await session.execute(
            select(TechnicalIndicator).where(TechnicalIndicator.stock_code == stock_code)
        )).scalars().all()

        for indicator in existing_indicators:
            await session.delete(indicator)

        await session.commit()
        print(f"\n⏳ 既存データを削除しました")

        # 株価データ保存
        print(f"⏳ 株価データをDBに保存中...")
        fetched_at = datetime.now()

        for _, row in df_prices.iterrows():
            price_record = StockPriceDaily(
                stock_code=stock_code,
                date=row["date"],
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=int(row["volume"]),
                turnover_value=Decimal(str(row["turnover_value"])),
                adjusted_open=Decimal(str(row["adjusted_open"])),
                adjusted_high=Decimal(str(row["adjusted_high"])),
                adjusted_low=Decimal(str(row["adjusted_low"])),
                adjusted_close=Decimal(str(row["adjusted_close"])),
                adjusted_volume=int(row["adjusted_volume"]),
                adjustment_factor=Decimal(str(row["adjustment_factor"])),
                is_upper_limit=False,
                is_lower_limit=False,
                fetched_at=fetched_at,
            )
            session.add(price_record)

        await session.commit()
        print(f"✅ 株価データをDBに保存しました（{len(df_prices)}件）")

        # テクニカル指標保存
        print(f"\n⏳ テクニカル指標をDBに保存中...")

        saved_count = 0
        error_count = 0

        for idx, row in df_technical.iterrows():
            try:
                # NaN/Infを None に変換
                indicator_record = TechnicalIndicator(
                    stock_code=stock_code,
                    date=row["date"],
                    calculated_at=row["date"],  # 計算日 = データ日付
                )

                # 各カラムを動的に設定（NaN/Infを除外）
                for col in df_technical.columns:
                    if col == "date":
                        continue

                    value = row[col]

                    # 型に応じて処理
                    if isinstance(value, str):
                        # 文字列はそのまま
                        pass
                    elif pd.isna(value):
                        # NaNはNone
                        value = None
                    elif isinstance(value, (np.integer, np.floating)):
                        # 数値型
                        if np.isinf(value):
                            value = None
                        elif col.startswith("is_"):
                            # boolean列は整数として保存
                            value = int(value)
                        else:
                            value = Decimal(str(round(float(value), 6)))

                    setattr(indicator_record, col, value)

                session.add(indicator_record)
                saved_count += 1

                # 進捗表示（10件ごと）
                if saved_count % 10 == 0:
                    print(f"  保存中... {saved_count}/{len(df_technical)}")

            except Exception as e:
                error_count += 1
                print(f"❌ エラー発生（行 {idx}）: {e}")
                if error_count <= 3:  # 最初の3件のみ詳細表示
                    print(f"   日付: {row['date']}")
                    print(f"   エラー詳細: {type(e).__name__}")
                continue

        try:
            await session.commit()
            print(f"✅ テクニカル指標をDBに保存しました（{saved_count}件）")
            if error_count > 0:
                print(f"⚠️  エラー件数: {error_count}件")
        except Exception as e:
            print(f"❌ commit時にエラー発生: {e}")
            await session.rollback()
            raise

    print(f"\n{'='*60}")
    print(f"✅ モックデータ生成完了！")
    print(f"{'='*60}\n")

    # サマリー表示
    print("📊 データサマリー:")
    print(f"  銘柄コード: {stock_code}")
    print(f"  期間: {df_prices['date'].min()} 〜 {df_prices['date'].max()}")
    print(f"  営業日数: {len(df_prices)}日")
    print(f"  株価データ: {len(df_prices)}件")
    print(f"  テクニカル指標: {len(df_technical)}件 × 125項目")
    print(f"\n  株価範囲:")
    print(f"    最高値: ¥{df_prices['high'].max():,.2f}")
    print(f"    最安値: ¥{df_prices['low'].min():,.2f}")
    print(f"    最新終値: ¥{df_prices['close'].iloc[-1]:,.2f}")
    print(f"    期間騰落率: {((df_prices['close'].iloc[-1] / df_prices['close'].iloc[0]) - 1) * 100:+.2f}%")


if __name__ == "__main__":
    asyncio.run(seed_stock_prices())
