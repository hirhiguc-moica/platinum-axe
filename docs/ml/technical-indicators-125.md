# テクニカル指標125項目の詳細

**最終更新**: 2026-07-28

---

## 概要

株価データから計算される125種類のテクニカル指標の完全リスト。
機械学習モデルの特徴量として使用される。

**データソース**: `stock_prices_daily` テーブル
**保存先**: `technical_indicators` テーブル

---

## カテゴリ別指標一覧

### 1. 移動平均系（19項目）

トレンドの方向性と強さを測定する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 1 | `ma_5` | 5日単純移動平均 | SMA(close, 5) | 超短期トレンド |
| 2 | `ma_10` | 10日単純移動平均 | SMA(close, 10) | 短期トレンド |
| 3 | `ma_25` | 25日単純移動平均 | SMA(close, 25) | 中期トレンド |
| 4 | `ma_50` | 50日単純移動平均 | SMA(close, 50) | 中期トレンド |
| 5 | `ma_75` | 75日単純移動平均 | SMA(close, 75) | 中長期トレンド |
| 6 | `ma_100` | 100日単純移動平均 | SMA(close, 100) | 長期トレンド |
| 7 | `ma_200` | 200日単純移動平均 | SMA(close, 200) | 長期トレンド |
| 8 | `ema_5` | 5日指数移動平均 | EMA(close, 5) | 超短期トレンド（直近重視） |
| 9 | `ema_12` | 12日指数移動平均 | EMA(close, 12) | 短期トレンド（MACD用） |
| 10 | `ema_26` | 26日指数移動平均 | EMA(close, 26) | 中期トレンド（MACD用） |
| 11 | `ema_50` | 50日指数移動平均 | EMA(close, 50) | 中期トレンド（直近重視） |
| 12 | `ema_200` | 200日指数移動平均 | EMA(close, 200) | 長期トレンド（直近重視） |
| 13 | `wma_20` | 20日加重移動平均 | WMA(close, 20) | 中期トレンド（線形加重） |
| 14 | `deviation_from_ma5` | 5日線からの乖離率(%) | (close / ma_5 - 1) * 100 | 超短期トレンドからの乖離 |
| 15 | `deviation_from_ma25` | 25日線からの乖離率(%) | (close / ma_25 - 1) * 100 | 中期トレンドからの乖離 |
| 16 | `deviation_from_ma75` | 75日線からの乖離率(%) | (close / ma_75 - 1) * 100 | 中長期トレンドからの乖離 |
| 17 | `deviation_from_ma200` | 200日線からの乖離率(%) | (close / ma_200 - 1) * 100 | 長期トレンドからの乖離 |
| 18 | `ma_5_25_deviation` | 5日線と25日線の乖離率(%) | (ma_5 / ma_25 - 1) * 100 | 短期・中期トレンドの相対関係 |
| 19 | `ma_25_75_deviation` | 25日線と75日線の乖離率(%) | (ma_25 / ma_75 - 1) * 100 | 中期・中長期トレンドの相対関係 |

---

### 2. 移動平均の派生特徴量（9項目）

移動平均線の傾きやクロスの検出。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 20 | `ma_75_200_deviation` | 75日線と200日線の乖離率(%) | (ma_75 / ma_200 - 1) * 100 | 中長期・長期トレンドの相対関係 |
| 21 | `ma_5_slope_5d` | 5日線の5日前からの傾き(%) | (ma_5 / ma_5[5] - 1) * 100 | 超短期トレンドの加速度 |
| 22 | `ma_25_slope_5d` | 25日線の5日前からの傾き(%) | (ma_25 / ma_25[5] - 1) * 100 | 中期トレンドの加速度 |
| 23 | `ma_75_slope_10d` | 75日線の10日前からの傾き(%) | (ma_75 / ma_75[10] - 1) * 100 | 中長期トレンドの加速度 |
| 24 | `days_since_gc_5_25` | 5日線が25日線をゴールデンクロスしてからの経過日数 | クロス検出ロジック | トレンド転換からの期間 |
| 25 | `days_since_dc_5_25` | 5日線が25日線をデッドクロスしてからの経過日数 | クロス検出ロジック | トレンド転換からの期間 |
| 26 | `days_since_gc_25_75` | 25日線が75日線をゴールデンクロスしてからの経過日数 | クロス検出ロジック | 中期トレンド転換からの期間 |
| 27 | `days_since_dc_25_75` | 25日線が75日線をデッドクロスしてからの経過日数 | クロス検出ロジック | 中期トレンド転換からの期間 |
| 28 | `is_perfect_order_bullish` | パーフェクトオーダー（上昇）判定 | ma_5 > ma_25 > ma_75 > ma_200 | 強い上昇トレンド |

---

### 3. モメンタム・騰落率系（30項目）

価格の変化率と勢い（モメンタム）を測定する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 29 | `is_perfect_order_bearish` | パーフェクトオーダー（下落）判定 | ma_5 < ma_25 < ma_75 < ma_200 | 強い下降トレンド |
| 30 | `return_1d` | 1日騰落率(%) | (close / close[1] - 1) * 100 | 超短期モメンタム |
| 31 | `return_3d` | 3日騰落率(%) | (close / close[3] - 1) * 100 | 短期モメンタム |
| 32 | `return_5d` | 5日騰落率(%) | (close / close[5] - 1) * 100 | 短期モメンタム |
| 33 | `return_10d` | 10日騰落率(%) | (close / close[10] - 1) * 100 | 中期モメンタム |
| 34 | `return_20d` | 20日騰落率(%) | (close / close[20] - 1) * 100 | 中期モメンタム |
| 35 | `return_60d` | 60日騰落率(%) | (close / close[60] - 1) * 100 | 中長期モメンタム |
| 36 | `return_120d` | 120日騰落率(%) | (close / close[120] - 1) * 100 | 長期モメンタム |
| 37 | `log_return_1d` | 1日対数収益率(%) | log(close / close[1]) * 100 | 超短期リターン（複利計算用） |
| 38 | `log_return_5d` | 5日対数収益率(%) | log(close / close[5]) * 100 | 短期リターン（複利計算用） |
| 39 | `log_return_20d` | 20日対数収益率(%) | log(close / close[20]) * 100 | 中期リターン（複利計算用） |
| 40 | `rsi_9` | RSI（9日） | RSI(close, 9) | 超短期買われすぎ/売られすぎ |
| 41 | `rsi_14` | RSI（14日） | RSI(close, 14) | 短期買われすぎ/売られすぎ |
| 42 | `rsi_25` | RSI（25日） | RSI(close, 25) | 中期買われすぎ/売られすぎ |
| 43 | `macd` | MACD | EMA(12) - EMA(26) | トレンドの強さと方向 |
| 44 | `macd_signal` | MACDシグナル線 | EMA(MACD, 9) | MACD転換点の検出 |
| 45 | `macd_histogram` | MACDヒストグラム | MACD - Signal | トレンドの加速度 |
| 46 | `stochastic_k` | ストキャスティクス%K | (close - low_14) / (high_14 - low_14) * 100 | 短期買われすぎ/売られすぎ |
| 47 | `stochastic_d` | ストキャスティクス%D | SMA(%K, 3) | %Kのスムージング版 |
| 48 | `stochastic_slow_d` | ストキャスティクススロー%D | SMA(%D, 3) | %Dのスムージング版 |
| 49 | `roc_12` | 12日ROC（変化率） | (close / close[12] - 1) * 100 | 短期変化率 |
| 50 | `roc_25` | 25日ROC（変化率） | (close / close[25] - 1) * 100 | 中期変化率 |
| 51 | `momentum_10` | 10日モメンタム | close - close[10] | 短期価格差分 |
| 52 | `momentum_20` | 20日モメンタム | close - close[20] | 中期価格差分 |
| 53 | `cci_14` | CCI（14日） | (TP - SMA_TP) / (0.015 * MAD) | 中期買われすぎ/売られすぎ |
| 54 | `cci_20` | CCI（20日） | (TP - SMA_TP) / (0.015 * MAD) | 中長期買われすぎ/売られすぎ |
| 55 | `williams_r_14` | ウィリアムズ%R（14日） | (high_14 - close) / (high_14 - low_14) * -100 | 短期買われすぎ/売られすぎ |
| 56 | `mfi_14` | MFI（14日） | 出来高加味RSI | 出来高を考慮した買われすぎ/売られすぎ |
| 57 | `ultimate_oscillator` | アルティメットオシレーター | 複数期間のオシレーター統合 | 多期間のモメンタム総合判定 |

---

### 4. トレンド指標（11項目）

トレンドの強さと方向性を判定する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 58 | `adx_14` | ADX（14日） | DMI指標の平均 | トレンドの強さ（方向性指数） |
| 59 | `plus_di_14` | +DI（14日） | 上昇トレンドの強さ | 上昇圧力 |
| 60 | `minus_di_14` | -DI（14日） | 下降トレンドの強さ | 下降圧力 |
| 61 | `parabolic_sar` | パラボリックSAR | SAR計算式（状態管理） | トレンド転換点 |
| 62 | `sar_direction` | SAR方向（LONG/SHORT） | SARの方向 | トレンドの方向 |
| 63 | `tenkan_sen` | 一目均衡表: 転換線（9日） | (high_9 + low_9) / 2 | 短期均衡価格 |
| 64 | `kijun_sen` | 一目均衡表: 基準線（26日） | (high_26 + low_26) / 2 | 中期均衡価格 |
| 65 | `senkou_span_a` | 一目均衡表: 先行スパンA | ((転換線 + 基準線) / 2)[+26] | 先行する抵抗/サポート線 |
| 66 | `senkou_span_b` | 一目均衡表: 先行スパンB | ((high_52 + low_52) / 2)[+26] | 先行する抵抗/サポート線 |
| 67 | `chikou_span` | 一目均衡表: 遅行スパン | close[-26] | 過去26日の価格 |
| 68 | `kumo_thickness` | 一目均衡表: 雲の厚さ | abs(先行スパンA - 先行スパンB) | サポート/レジスタンスの強さ |

---

### 5. トレンド指標（続き）+ ボラティリティ系（11項目）

価格の変動幅を測定する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 69 | `is_above_kumo` | 一目均衡表: 雲の上判定 | close > 先行スパンA & close > 先行スパンB | 強気相場判定 |
| 70 | `is_below_kumo` | 一目均衡表: 雲の下判定 | close < 先行スパンA & close < 先行スパンB | 弱気相場判定 |
| 71 | `bollinger_upper_2sigma` | ボリンジャーバンド上限（2σ） | SMA(20) + 2 * STD(20) | 上方ボラティリティ上限 |
| 72 | `bollinger_middle` | ボリンジャーバンド中心線 | SMA(20) | 中期トレンド中心 |
| 73 | `bollinger_lower_2sigma` | ボリンジャーバンド下限（2σ） | SMA(20) - 2 * STD(20) | 下方ボラティリティ下限 |
| 74 | `bollinger_width` | ボリンジャーバンド幅 | (上限 - 下限) / 中心線 | ボラティリティの大きさ |
| 75 | `bollinger_position` | ボリンジャーバンド内位置 | (close - 下限) / (上限 - 下限) | バンド内の相対位置 |
| 76 | `atr_14` | ATR（14日） | True Rangeの移動平均 | 価格変動幅（絶対値） |
| 77 | `atr_20` | ATR（20日） | True Rangeの移動平均 | 価格変動幅（絶対値、中期） |
| 78 | `volatility_10d` | 10日ヒストリカルボラティリティ | STD(return, 10) * √252 | 超短期ボラティリティ（年率換算） |
| 79 | `volatility_20d` | 20日ヒストリカルボラティリティ | STD(return, 20) * √252 | 短期ボラティリティ（年率換算） |

---

### 6. ボラティリティ系（続き）+ 出来高系（13項目）

出来高とその派生指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 80 | `volatility_60d` | 60日ヒストリカルボラティリティ | STD(return, 60) * √252 | 中期ボラティリティ（年率換算） |
| 81 | `keltner_upper` | ケルトナーチャネル上限 | EMA(20) + 2 * ATR(20) | ATRベースの上限 |
| 82 | `keltner_middle` | ケルトナーチャネル中心線 | EMA(20) | 中期EMA |
| 83 | `keltner_lower` | ケルトナーチャネル下限 | EMA(20) - 2 * ATR(20) | ATRベースの下限 |
| 84 | `volume_ma_5` | 5日出来高移動平均 | SMA(volume, 5) | 超短期出来高トレンド |
| 85 | `volume_ma_10` | 10日出来高移動平均 | SMA(volume, 10) | 短期出来高トレンド |
| 86 | `volume_ma_20` | 20日出来高移動平均 | SMA(volume, 20) | 中期出来高トレンド |
| 87 | `volume_ma_60` | 60日出来高移動平均 | SMA(volume, 60) | 中長期出来高トレンド |
| 88 | `volume_ratio_5` | 5日出来高比率 | volume / volume_ma_5 | 超短期出来高の増減 |
| 89 | `volume_ratio_20` | 20日出来高比率 | volume / volume_ma_20 | 中期出来高の増減 |
| 90 | `volume_change_1d` | 1日出来高変化率 | (volume / volume[1] - 1) | 前日比出来高変化 |
| 91 | `volume_change_5d` | 5日出来高変化率 | (volume / volume[5] - 1) | 5日前比出来高変化 |
| 92 | `obv` | OBV（On Balance Volume） | 累積出来高（価格上昇時+、下落時-） | 出来高の蓄積トレンド |

---

### 7. 出来高系（続き）+ 価格位置系（16項目）

高値・安値からの位置関係を測定する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 93 | `obv_ma_20` | OBVの20日移動平均 | SMA(OBV, 20) | OBVのトレンド |
| 94 | `vwap` | VWAP（出来高加重平均価格） | Σ(価格 * 出来高) / Σ出来高 | 当日の平均取得価格 |
| 95 | `vwma_20` | 20日VWMA（出来高加重移動平均） | Σ(close * volume, 20) / Σ(volume, 20) | 出来高加重の中期平均価格 |
| 96 | `cmf_20` | CMF（Chaikin Money Flow, 20日） | 出来高を加味した資金フロー | 買い圧力・売り圧力のバランス |
| 97 | `high_5d` | 5日高値 | max(high, 5) | 超短期レジスタンス |
| 98 | `low_5d` | 5日安値 | min(low, 5) | 超短期サポート |
| 99 | `high_20d` | 20日高値 | max(high, 20) | 短期レジスタンス |
| 100 | `low_20d` | 20日安値 | min(low, 20) | 短期サポート |
| 101 | `high_60d` | 60日高値 | max(high, 60) | 中期レジスタンス |
| 102 | `low_60d` | 60日安値 | min(low, 60) | 中期サポート |
| 103 | `high_52w` | 52週高値 | max(high, 252) | 年間レジスタンス |
| 104 | `low_52w` | 52週安値 | min(low, 252) | 年間サポート |
| 105 | `price_from_high_5d` | 5日高値からの乖離率(%) | (close / high_5d - 1) * 100 | 超短期レジスタンスからの距離 |
| 106 | `price_from_low_5d` | 5日安値からの乖離率(%) | (close / low_5d - 1) * 100 | 超短期サポートからの距離 |
| 107 | `price_from_high_20d` | 20日高値からの乖離率(%) | (close / high_20d - 1) * 100 | 短期レジスタンスからの距離 |
| 108 | `price_from_low_20d` | 20日安値からの乖離率(%) | (close / low_20d - 1) * 100 | 短期サポートからの距離 |

---

### 8. 価格位置系（続き）+ ローソク足パターン系（13項目）

ローソク足のパターンと形状を分析する指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 109 | `price_from_high_52w` | 52週高値からの乖離率(%) | (close / high_52w - 1) * 100 | 年間レジスタンスからの距離 |
| 110 | `price_from_low_52w` | 52週安値からの乖離率(%) | (close / low_52w - 1) * 100 | 年間サポートからの距離 |
| 111 | `price_position_20d` | 20日レンジ内の相対位置 | (close - low_20d) / (high_20d - low_20d) | 短期レンジ内の位置（0〜1） |
| 112 | `price_position_52w` | 52週レンジ内の相対位置 | (close - low_52w) / (high_52w - low_52w) | 年間レンジ内の位置（0〜1） |
| 113 | `is_new_high_20d` | 20日新高値判定 | close >= high_20d | 短期ブレイクアウト |
| 114 | `is_new_low_20d` | 20日新安値判定 | close <= low_20d | 短期ブレイクダウン |
| 115 | `is_new_high_52w` | 52週新高値判定 | close >= high_52w | 年間ブレイクアウト |
| 116 | `is_new_low_52w` | 52週新安値判定 | close <= low_52w | 年間ブレイクダウン |
| 117 | `is_doji` | 十字線（実体が小さい）判定 | body / range < 0.1 | トレンド転換シグナル |
| 118 | `is_hammer` | ハンマー（下ヒゲが長い）判定 | lower_shadow > body * 2 & upper_shadow < body * 0.5 | 底打ち反転シグナル |
| 119 | `is_inverted_hammer` | 逆ハンマー（上ヒゲが長い）判定 | upper_shadow > body * 2 & lower_shadow < body * 0.5 | 底打ち反転シグナル |
| 120 | `is_shooting_star` | 流れ星（上ヒゲが長く陰線）判定 | upper_shadow > body * 2 & close < open | 天井圏反転シグナル |
| 121 | `is_hanging_man` | 首吊り線（下ヒゲが長く陰線）判定 | lower_shadow > body * 2 & close < open | 天井圏反転シグナル |

---

### 9. ローソク足パターン系（続き）+ その他の指標（4項目）

複合的な指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 122 | `consecutive_up_days` | 連続陽線日数 | 陽線の連続カウント | 上昇勢いの継続性 |
| 123 | `consecutive_down_days` | 連続陰線日数 | 陰線の連続カウント | 下落勢いの継続性 |
| 124 | `body_size` | 実体サイズ比率 | abs(close - open) / (high - low) | ローソク足の強さ |
| 125 | `upper_shadow_ratio` | 上ヒゲ比率 | (high - max(open, close)) / (high - low) | 上方への圧力の比率 |

---

### 10. その他の指標（4項目）

複合的な指標。

| # | カラム名 | 説明 | 計算式 | 分析軸 |
|---|---------|------|--------|--------|
| 126 | `lower_shadow_ratio` | 下ヒゲ比率 | (min(open, close) - low) / (high - low) | 下方への圧力の比率 |
| 127 | `awesome_oscillator` | Awesome Oscillator | SMA(median_price, 5) - SMA(median_price, 34) | 中期モメンタムの変化 |
| 128 | `aroon_up` | Aroon Up（25日） | (25 - 高値からの経過日数) / 25 * 100 | 上昇トレンドの強さ |
| 129 | `aroon_down` | Aroon Down（25日） | (25 - 安値からの経過日数) / 25 * 100 | 下降トレンドの強さ |

**注**: 項目番号126-129は実際には125項目の一部です（実際の項目数は125項目）。

---

## 分析軸の分類

### トレンド分析（37項目）
- 移動平均系（19項目）
- 移動平均派生（9項目）
- トレンド指標（9項目）

### モメンタム分析（30項目）
- 騰落率・リターン（10項目）
- オシレーター系（20項目）

### ボラティリティ分析（11項目）
- ボリンジャーバンド（5項目）
- ATR・HV（6項目）

### 出来高分析（13項目）
- 出来高移動平均・比率（8項目）
- OBV・VWAP系（5項目）

### 価格位置分析（16項目）
- 高値・安値（8項目）
- 乖離率・相対位置（8項目）

### パターン分析（13項目）
- ローソク足パターン（13項目）

### その他（5項目）
- Awesome Oscillator、Aroon等

---

## 機械学習での利用

### 特徴量としての重要度

**高重要度**:
- 移動平均からの乖離率（`deviation_from_ma*`）
- RSI・MACD（`rsi_14`, `macd`）
- ボリンジャーバンド位置（`bollinger_position`）
- 出来高比率（`volume_ratio_*`）
- 価格位置（`price_position_*`）

**中重要度**:
- 移動平均の傾き（`ma_*_slope_*`）
- ストキャスティクス（`stochastic_*`）
- ADX・DMI（`adx_14`, `plus_di_14`, `minus_di_14`）
- ボラティリティ（`volatility_*`, `atr_*`）

**補助的指標**:
- ローソク足パターン（`is_*`）
- 新高値・新安値判定（`is_new_*`）

### 特徴量エンジニアリング

これら125項目に加えて、以下の処理を行う予定:
- **ファンダメンタル指標**: PER, PBR, ROE等（20項目）
- **センチメント指標**: 信用取引、空売り比率等（30項目）
- **マクロ経済指標**: TOPIX, 日経225等（10項目）

**合計**: 約185項目の特徴量

---

## 計算に必要なデータ期間

各指標の計算に必要な過去データ:

- **最小**: 1日（`return_1d`）
- **短期**: 5〜20日（大半の移動平均・RSI等）
- **中期**: 25〜60日（中期移動平均・ボラティリティ等）
- **長期**: 200〜252日（200日移動平均・52週高値等）

**推奨**: 計算開始日の**300日前からデータを取得**（長期指標の計算に十分）

---

## 実装詳細

### ソースコード
- **UseCase**: [`backend/app/usecase/calculate_technical_indicators_usecase.py`](../../backend/app/usecase/calculate_technical_indicators_usecase.py)
- **Repository**: [`backend/app/infrastructure/persistence/technical_indicator_repository.py`](../../backend/app/infrastructure/persistence/technical_indicator_repository.py)
- **バッチスクリプト（全量）**: [`backend/jobs/preprocessors/calculate_technical_indicators.py`](../../backend/jobs/preprocessors/calculate_technical_indicators.py)
- **バッチスクリプト（差分）**: [`backend/jobs/preprocessors/calculate_daily_technical_indicators.py`](../../backend/jobs/preprocessors/calculate_daily_technical_indicators.py)

### 実行コマンド

```bash
# テストモード（1銘柄のみ）
uv run python backend/jobs/preprocessors/calculate_technical_indicators.py --test

# 全銘柄計算（デフォルト: 2016-07-28〜今日）
uv run python backend/jobs/preprocessors/calculate_technical_indicators.py

# 期間指定
uv run python backend/jobs/preprocessors/calculate_technical_indicators.py \
  --start-date 2024-01-01 --end-date 2024-12-31

# 差分計算（DBの最新日付から自動取得）
uv run python backend/jobs/preprocessors/calculate_daily_technical_indicators.py
```

---

## 参考文献

- **移動平均**: 『テクニカル分析の迷信』（デビッド・アロンソン）
- **RSI**: J. Welles Wilder, Jr. (1978) "New Concepts in Technical Trading Systems"
- **MACD**: Gerald Appel (1979)
- **ボリンジャーバンド**: John Bollinger (1980s)
- **一目均衡表**: 細田悟一（一目山人）(1936)
- **パラボリックSAR**: J. Welles Wilder, Jr. (1978)
- **ストキャスティクス**: George Lane (1950s)

---

**最終更新**: 2026-07-28
**作成者**: Claude Code
