# データベーススキーマ設計

## 設計方針

### 原則

✅ **J-Quants APIから取得した全データをDBに格納する**

- API依存の低減（過去データ再取得不要）
- パフォーマンス向上（DBクエリの方が高速）
- データ整合性の保証
- APIコスト削減

### データレイヤー構造

```
【Layer 1】Raw Data（トランザクションデータ）
  └─ J-Quants APIから取得した生データをそのまま保存

【Layer 2】Derived Data（計算済みデータ）
  └─ テクニカル指標を事前計算してDB保存

【Layer 3】Feature Store（機械学習用特徴量）
  └─ モデル学習・推論用に最適化されたデータ

【Layer 4】Prediction & Result（予測・結果）
  └─ ラウンド推奨・デイリーシグナル・実績データ
```

---

## Layer 1: Raw Data（J-Quants API生データ）

### 1. 株価データ

#### 1.1. stock_prices_daily（株価日次四本値）

**API**: `/equities/bars/daily`

```sql
CREATE TABLE stock_prices_daily (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_code VARCHAR(10) NOT NULL,           -- 銘柄コード
    date DATE NOT NULL,                         -- 日付

    -- 四本値（調整前）
    open DECIMAL(10,2),                         -- 始値
    high DECIMAL(10,2),                         -- 高値
    low DECIMAL(10,2),                          -- 安値
    close DECIMAL(10,2),                        -- 終値
    volume BIGINT,                              -- 出来高
    turnover_value DECIMAL(15,2),               -- 売買代金

    -- 調整済み四本値
    adjusted_open DECIMAL(10,2),                -- 調整後始値
    adjusted_high DECIMAL(10,2),                -- 調整後高値
    adjusted_low DECIMAL(10,2),                 -- 調整後安値
    adjusted_close DECIMAL(10,2),               -- 調整後終値
    adjusted_volume BIGINT,                     -- 調整後出来高
    adjustment_factor DECIMAL(10,6),            -- 調整係数

    -- ストップ高/安フラグ
    is_upper_limit BOOLEAN DEFAULT FALSE,       -- ストップ高
    is_lower_limit BOOLEAN DEFAULT FALSE,       -- ストップ安

    -- メタ情報
    fetched_at TIMESTAMP NOT NULL,              -- API取得日時
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_code, date)
);

CREATE INDEX idx_stock_prices_daily_code_date ON stock_prices_daily(stock_code, date DESC);
CREATE INDEX idx_stock_prices_daily_date ON stock_prices_daily(date DESC);
```

#### 1.2. stock_prices_am（前場四本値）

**API**: `/equities/bars/daily/am`

```sql
CREATE TABLE stock_prices_am (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    turnover_value DECIMAL(15,2),
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, date)
);

CREATE INDEX idx_stock_prices_am_code_date ON stock_prices_am(stock_code, date DESC);
```

#### 1.3. stock_prices_minute（分足データ）※アドオン

**API**: `/equities/bars/minute`

```sql
CREATE TABLE stock_prices_minute (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    datetime TIMESTAMP NOT NULL,                -- 分足の日時
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, datetime)
);

CREATE INDEX idx_stock_prices_minute_code_datetime ON stock_prices_minute(stock_code, datetime DESC);
```

#### 1.4. stock_trades（ティックデータ）※アドオン

**API**: `/equities/trades`

```sql
CREATE TABLE stock_trades (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    datetime TIMESTAMP NOT NULL,                -- 約定日時
    price DECIMAL(10,2) NOT NULL,               -- 約定価格
    volume INT NOT NULL,                        -- 約定数量
    side VARCHAR(10),                           -- 売買区分（BUY/SELL）
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, datetime, price, volume)
);

CREATE INDEX idx_stock_trades_code_datetime ON stock_trades(stock_code, datetime DESC);
```

---

### 2. 銘柄マスタ

#### 2.1. stock_master（銘柄マスタ）

**API**: `/equities/list`

```sql
CREATE TABLE stock_master (
    stock_code VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,         -- 会社名
    company_name_en VARCHAR(255),               -- 英語名
    sector_code VARCHAR(10),                    -- 業種コード（33業種分類）
    sector_name VARCHAR(100),                   -- 業種名
    market_code VARCHAR(10),                    -- 市場区分コード
    market_name VARCHAR(50),                    -- 市場名（プライム/スタンダード等）
    listing_date DATE,                          -- 上場日
    delisting_date DATE,                        -- 上場廃止日
    is_active BOOLEAN DEFAULT TRUE,             -- 上場中フラグ
    market_cap DECIMAL(15,2),                   -- 時価総額（最新）
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_stock_master_sector ON stock_master(sector_code);
CREATE INDEX idx_stock_master_market ON stock_master(market_code);
CREATE INDEX idx_stock_master_is_active ON stock_master(is_active);
```

---

### 3. 財務情報

#### 3.1. financial_statements（財務諸表）

**API**: `/fins/summary`, `/fins/details`

```sql
CREATE TABLE financial_statements (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,                   -- 会計年度
    fiscal_quarter VARCHAR(2) NOT NULL,         -- Q1/Q2/Q3/Q4/FY（通期）
    announcement_date DATE,                     -- 決算発表日
    period_start DATE,                          -- 期間開始日
    period_end DATE,                            -- 期間終了日

    -- 損益計算書（PL）
    revenue DECIMAL(15,2),                      -- 売上高
    operating_profit DECIMAL(15,2),             -- 営業利益
    ordinary_profit DECIMAL(15,2),              -- 経常利益
    net_income DECIMAL(15,2),                   -- 当期純利益
    earnings_per_share DECIMAL(10,2),           -- EPS（1株当たり利益）

    -- 貸借対照表（BS）
    total_assets DECIMAL(15,2),                 -- 総資産
    current_assets DECIMAL(15,2),               -- 流動資産
    fixed_assets DECIMAL(15,2),                 -- 固定資産
    total_liabilities DECIMAL(15,2),            -- 負債合計
    current_liabilities DECIMAL(15,2),          -- 流動負債
    fixed_liabilities DECIMAL(15,2),            -- 固定負債
    total_equity DECIMAL(15,2),                 -- 純資産
    book_value_per_share DECIMAL(10,2),         -- BPS（1株当たり純資産）

    -- キャッシュフロー計算書（CF）
    operating_cf DECIMAL(15,2),                 -- 営業CF
    investing_cf DECIMAL(15,2),                 -- 投資CF
    financing_cf DECIMAL(15,2),                 -- 財務CF
    free_cash_flow DECIMAL(15,2),               -- フリーCF

    -- 財務指標
    roe DECIMAL(8,4),                           -- ROE（自己資本利益率）
    roa DECIMAL(8,4),                           -- ROA（総資産利益率）
    equity_ratio DECIMAL(8,4),                  -- 自己資本比率
    debt_ratio DECIMAL(8,4),                    -- 負債比率
    current_ratio DECIMAL(8,4),                 -- 流動比率

    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, fiscal_year, fiscal_quarter)
);

CREATE INDEX idx_financial_statements_code_year ON financial_statements(stock_code, fiscal_year DESC);
CREATE INDEX idx_financial_statements_announcement ON financial_statements(announcement_date DESC);
```

#### 3.2. dividend_info（配当情報）

**API**: `/fins/dividend`

```sql
CREATE TABLE dividend_info (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,
    announcement_date DATE,                     -- 発表日
    ex_dividend_date DATE,                      -- 権利落ち日
    payment_date DATE,                          -- 配当支払日
    dividend_per_share DECIMAL(10,2),           -- 1株当たり配当金
    dividend_type VARCHAR(20),                  -- 配当種別（期末/中間等）
    dividend_yield DECIMAL(8,4),                -- 配当利回り
    payout_ratio DECIMAL(8,4),                  -- 配当性向
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, fiscal_year, dividend_type)
);

CREATE INDEX idx_dividend_info_code_year ON dividend_info(stock_code, fiscal_year DESC);
CREATE INDEX idx_dividend_info_ex_date ON dividend_info(ex_dividend_date DESC);
```

#### 3.3. stock_splits（株式分割）

**API**: `/fins/announcement` 等から取得

```sql
CREATE TABLE stock_splits (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    announcement_date DATE NOT NULL,            -- 発表日
    effective_date DATE NOT NULL,               -- 効力発生日
    split_ratio DECIMAL(10,4) NOT NULL,         -- 分割比率（例: 1株→2株 = 2.0）
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, effective_date)
);

CREATE INDEX idx_stock_splits_code_date ON stock_splits(stock_code, effective_date DESC);
```

#### 3.4. earnings_calendar（決算発表予定）

**API**: `/equities/earnings-calendar`

```sql
CREATE TABLE earnings_calendar (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,
    fiscal_quarter VARCHAR(2) NOT NULL,
    scheduled_date DATE,                        -- 発表予定日
    is_announced BOOLEAN DEFAULT FALSE,         -- 発表済みフラグ
    actual_date DATE,                           -- 実際の発表日
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, fiscal_year, fiscal_quarter)
);

CREATE INDEX idx_earnings_calendar_scheduled ON earnings_calendar(scheduled_date);
CREATE INDEX idx_earnings_calendar_code ON earnings_calendar(stock_code, fiscal_year DESC);
```

---

### 4. 信用取引データ

#### 4.1. margin_trading_daily（日々公表信用取引残高）

**API**: `/markets/margin-alert`

```sql
CREATE TABLE margin_trading_daily (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,

    -- 信用買い
    margin_buy_balance BIGINT,                  -- 信用買い残（株数）
    margin_buy_value DECIMAL(15,2),             -- 信用買い残金額
    margin_buy_new BIGINT,                      -- 当日新規買い
    margin_buy_repayment BIGINT,                -- 当日返済買い

    -- 信用売り
    margin_sell_balance BIGINT,                 -- 信用売り残（株数）
    margin_sell_value DECIMAL(15,2),            -- 信用売り残金額
    margin_sell_new BIGINT,                     -- 当日新規売り
    margin_sell_repayment BIGINT,               -- 当日返済売り

    -- 規制情報
    is_daily_publication BOOLEAN,               -- 日々公表銘柄フラグ
    margin_requirement_ratio DECIMAL(5,2),      -- 委託保証金率（規制時）
    regulation_type VARCHAR(50),                -- 規制区分
    regulation_start_date DATE,                 -- 規制開始日

    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, date)
);

CREATE INDEX idx_margin_trading_daily_code_date ON margin_trading_daily(stock_code, date DESC);
CREATE INDEX idx_margin_trading_daily_regulation ON margin_trading_daily(is_daily_publication, date DESC);
```

#### 4.2. margin_trading_weekly（信用取引週末残高）

**API**: `/markets/margin-interest`

```sql
CREATE TABLE margin_trading_weekly (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    week_end_date DATE NOT NULL,                -- 週末日付

    -- 制度信用
    system_margin_buy_balance BIGINT,           -- 制度信用買い残
    system_margin_buy_value DECIMAL(15,2),
    system_margin_sell_balance BIGINT,          -- 制度信用売り残
    system_margin_sell_value DECIMAL(15,2),

    -- 一般信用
    general_margin_buy_balance BIGINT,          -- 一般信用買い残
    general_margin_buy_value DECIMAL(15,2),
    general_margin_sell_balance BIGINT,         -- 一般信用売り残
    general_margin_sell_value DECIMAL(15,2),

    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, week_end_date)
);

CREATE INDEX idx_margin_trading_weekly_code_date ON margin_trading_weekly(stock_code, week_end_date DESC);
```

---

### 5. 市場センチメント

#### 5.1. short_selling_ratio（業種別空売り比率）

**API**: `/markets/short-ratio`

```sql
CREATE TABLE short_selling_ratio (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    sector_code VARCHAR(10),                    -- 業種コード（NULLの場合は全市場）
    sector_name VARCHAR(100),
    short_selling_ratio DECIMAL(5,2),           -- 空売り比率（%）
    short_selling_volume BIGINT,                -- 空売り数量
    total_volume BIGINT,                        -- 総売買高
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, sector_code)
);

CREATE INDEX idx_short_selling_ratio_date ON short_selling_ratio(date DESC);
CREATE INDEX idx_short_selling_ratio_sector ON short_selling_ratio(sector_code, date DESC);
```

#### 5.2. short_selling_report（空売り残高報告）

**API**: `/markets/short-sale-report`

```sql
CREATE TABLE short_selling_report (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    short_position BIGINT,                      -- 空売り残高（株数）
    short_position_ratio DECIMAL(5,2),          -- 空売り残高比率（対発行済株式数）
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, date)
);

CREATE INDEX idx_short_selling_report_code_date ON short_selling_report(stock_code, date DESC);
```

#### 5.3. investor_trading（投資部門別売買動向）

**API**: `/equities/investor-types`

```sql
CREATE TABLE investor_trading (
    id BIGSERIAL PRIMARY KEY,
    week_end_date DATE NOT NULL,                -- 週末日付
    investor_type VARCHAR(50) NOT NULL,         -- 投資家区分（個人/外国人/信託銀行等）
    market_section VARCHAR(20),                 -- 市場区分（プライム/スタンダード等）

    -- 現物
    spot_buy_volume BIGINT,                     -- 現物買い数量
    spot_buy_value DECIMAL(15,2),               -- 現物買い金額
    spot_sell_volume BIGINT,                    -- 現物売り数量
    spot_sell_value DECIMAL(15,2),              -- 現物売り金額
    spot_net_value DECIMAL(15,2),               -- 現物差引（買い - 売り）

    -- 信用
    margin_buy_volume BIGINT,
    margin_buy_value DECIMAL(15,2),
    margin_sell_volume BIGINT,
    margin_sell_value DECIMAL(15,2),
    margin_net_value DECIMAL(15,2),

    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_end_date, investor_type, market_section)
);

CREATE INDEX idx_investor_trading_date ON investor_trading(week_end_date DESC);
CREATE INDEX idx_investor_trading_type ON investor_trading(investor_type, week_end_date DESC);
```

#### 5.4. trading_breakdown（売買内訳）

**API**: `/markets/breakdown`

```sql
CREATE TABLE trading_breakdown (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    trading_value DECIMAL(15,2),                -- 売買代金
    morning_trading_value DECIMAL(15,2),        -- 前場売買代金
    afternoon_trading_value DECIMAL(15,2),      -- 後場売買代金
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, stock_code)
);

CREATE INDEX idx_trading_breakdown_date ON trading_breakdown(date DESC);
CREATE INDEX idx_trading_breakdown_code ON trading_breakdown(stock_code, date DESC);
```

---

### 6. 指数データ

#### 6.1. index_prices_daily（指数日次四本値）

**API**: `/indices/bars/daily`, `/indices/bars/daily/topix`

```sql
CREATE TABLE index_prices_daily (
    id BIGSERIAL PRIMARY KEY,
    index_code VARCHAR(20) NOT NULL,            -- 指数コード（TOPIX/NIKKEI225等）
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,                              -- 出来高（該当する場合）
    turnover_value DECIMAL(15,2),               -- 売買代金
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(index_code, date)
);

CREATE INDEX idx_index_prices_daily_code_date ON index_prices_daily(index_code, date DESC);
```

#### 6.2. sector_indices（業種別指数）

**API**: `/indices/bars/daily` 等から33業種分を取得

```sql
CREATE TABLE sector_indices (
    id BIGSERIAL PRIMARY KEY,
    sector_code VARCHAR(10) NOT NULL,           -- 業種コード
    sector_name VARCHAR(100) NOT NULL,          -- 業種名
    date DATE NOT NULL,
    index_value DECIMAL(10,2),                  -- 指数値
    change_rate DECIMAL(8,4),                   -- 騰落率
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sector_code, date)
);

CREATE INDEX idx_sector_indices_code_date ON sector_indices(sector_code, date DESC);
CREATE INDEX idx_sector_indices_date ON sector_indices(date DESC);
```

#### 6.3. topix_components（TOPIX構成銘柄）

**API**: `/indices/topix/weight` 等

```sql
CREATE TABLE topix_components (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    effective_date DATE NOT NULL,               -- 適用開始日
    weight DECIMAL(10,6),                       -- 構成比率
    is_current BOOLEAN DEFAULT TRUE,            -- 現在構成銘柄フラグ
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, effective_date)
);

CREATE INDEX idx_topix_components_code ON topix_components(stock_code, effective_date DESC);
CREATE INDEX idx_topix_components_current ON topix_components(is_current, stock_code);
```

---

### 7. デリバティブ（将来的に追加）

#### 7.1. futures_prices（先物四本値）

**API**: `/derivatives/bars/daily/futures`

```sql
CREATE TABLE futures_prices (
    id BIGSERIAL PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL,          -- 商品コード
    contract_month VARCHAR(6) NOT NULL,         -- 限月（YYYYMM）
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    open_interest BIGINT,                       -- 建玉
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_code, contract_month, date)
);

CREATE INDEX idx_futures_prices_code_date ON futures_prices(product_code, contract_month, date DESC);
```

#### 7.2. options_prices（オプション四本値）

**API**: `/derivatives/bars/daily/options`

```sql
CREATE TABLE options_prices (
    id BIGSERIAL PRIMARY KEY,
    product_code VARCHAR(20) NOT NULL,
    contract_month VARCHAR(6) NOT NULL,
    strike_price DECIMAL(10,2) NOT NULL,        -- 権利行使価格
    option_type VARCHAR(4) NOT NULL,            -- CALL/PUT
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    open_interest BIGINT,
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_code, contract_month, strike_price, option_type, date)
);

CREATE INDEX idx_options_prices_code_date ON options_prices(product_code, contract_month, date DESC);
```

---

### 8. その他マスタ・カレンダー

#### 8.1. trading_calendar（取引カレンダー）

**API**: `/markets/calendar`

```sql
CREATE TABLE trading_calendar (
    date DATE PRIMARY KEY,
    is_trading_day BOOLEAN NOT NULL,            -- 取引日かどうか
    holiday_name VARCHAR(100),                  -- 休日名（該当する場合）
    market_section VARCHAR(20),                 -- 市場区分
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_trading_calendar_is_trading ON trading_calendar(is_trading_day, date DESC);
```

---

## Layer 2: Derived Data（計算済みデータ）

### 9. technical_indicators（テクニカル指標）

```sql
CREATE TABLE technical_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,

    -- ==========================================
    -- 1. 移動平均線
    -- ==========================================
    -- 単純移動平均（SMA）
    ma_5 DECIMAL(10,2),                         -- 5日移動平均
    ma_10 DECIMAL(10,2),                        -- 10日移動平均
    ma_25 DECIMAL(10,2),                        -- 25日移動平均
    ma_50 DECIMAL(10,2),                        -- 50日移動平均
    ma_75 DECIMAL(10,2),                        -- 75日移動平均
    ma_100 DECIMAL(10,2),                       -- 100日移動平均
    ma_200 DECIMAL(10,2),                       -- 200日移動平均

    -- 指数移動平均（EMA）
    ema_5 DECIMAL(10,2),                        -- 5日指数移動平均
    ema_12 DECIMAL(10,2),                       -- 12日指数移動平均
    ema_26 DECIMAL(10,2),                       -- 26日指数移動平均
    ema_50 DECIMAL(10,2),                       -- 50日指数移動平均
    ema_200 DECIMAL(10,2),                      -- 200日指数移動平均

    -- 加重移動平均（WMA）
    wma_20 DECIMAL(10,2),                       -- 20日加重移動平均

    -- ==========================================
    -- 2. 移動平均の派生特徴量
    -- ==========================================
    -- 乖離率（Deviation）
    deviation_from_ma5 DECIMAL(8,4),            -- (価格 - MA5) / MA5 × 100
    deviation_from_ma25 DECIMAL(8,4),           -- (価格 - MA25) / MA25 × 100
    deviation_from_ma75 DECIMAL(8,4),           -- (価格 - MA75) / MA75 × 100
    deviation_from_ma200 DECIMAL(8,4),          -- (価格 - MA200) / MA200 × 100

    -- 移動平均間の乖離率
    ma_5_25_deviation DECIMAL(8,4),             -- (MA5 - MA25) / MA25 × 100
    ma_25_75_deviation DECIMAL(8,4),            -- (MA25 - MA75) / MA75 × 100
    ma_75_200_deviation DECIMAL(8,4),           -- (MA75 - MA200) / MA200 × 100

    -- 移動平均の傾き（Slope）
    ma_5_slope_5d DECIMAL(8,4),                 -- 直近5日のMA5の傾き
    ma_25_slope_5d DECIMAL(8,4),                -- 直近5日のMA25の傾き
    ma_75_slope_10d DECIMAL(8,4),               -- 直近10日のMA75の傾き

    -- ゴールデンクロス/デッドクロスからの経過日数
    days_since_gc_5_25 INT,                     -- MA5×MA25 GCからの日数（NULL = 未発生）
    days_since_dc_5_25 INT,                     -- MA5×MA25 DCからの日数
    days_since_gc_25_75 INT,                    -- MA25×MA75 GCからの日数
    days_since_dc_25_75 INT,                    -- MA25×MA75 DCからの日数

    -- 移動平均の並び順（パーフェクトオーダー判定）
    is_perfect_order_bullish BOOLEAN,           -- MA5 > MA25 > MA75 > MA200
    is_perfect_order_bearish BOOLEAN,           -- MA5 < MA25 < MA75 < MA200

    -- ==========================================
    -- 3. 騰落率（Return）
    -- ==========================================
    return_1d DECIMAL(8,4),                     -- 1日騰落率
    return_3d DECIMAL(8,4),                     -- 3日騰落率
    return_5d DECIMAL(8,4),                     -- 5日騰落率
    return_10d DECIMAL(8,4),                    -- 10日騰落率
    return_20d DECIMAL(8,4),                    -- 20日騰落率
    return_60d DECIMAL(8,4),                    -- 60日騰落率
    return_120d DECIMAL(8,4),                   -- 120日騰落率

    -- 対数収益率（Log Return）
    log_return_1d DECIMAL(8,4),                 -- 1日対数収益率
    log_return_5d DECIMAL(8,4),                 -- 5日対数収益率
    log_return_20d DECIMAL(8,4),                -- 20日対数収益率

    -- ==========================================
    -- 4. モメンタム系
    -- ==========================================
    -- RSI（Relative Strength Index）
    rsi_9 DECIMAL(5,2),                         -- RSI(9日)
    rsi_14 DECIMAL(5,2),                        -- RSI(14日)
    rsi_25 DECIMAL(5,2),                        -- RSI(25日)

    -- MACD
    macd DECIMAL(10,4),                         -- MACD
    macd_signal DECIMAL(10,4),                  -- MACDシグナル
    macd_histogram DECIMAL(10,4),               -- MACDヒストグラム

    -- ストキャスティクス
    stochastic_k DECIMAL(5,2),                  -- %K
    stochastic_d DECIMAL(5,2),                  -- %D
    stochastic_slow_d DECIMAL(5,2),             -- Slow %D

    -- ROC（Rate of Change）
    roc_12 DECIMAL(8,4),                        -- 12日ROC
    roc_25 DECIMAL(8,4),                        -- 25日ROC

    -- モメンタム
    momentum_10 DECIMAL(10,4),                  -- 10日モメンタム
    momentum_20 DECIMAL(10,4),                  -- 20日モメンタム

    -- CCI（Commodity Channel Index）
    cci_14 DECIMAL(8,2),                        -- 14日CCI
    cci_20 DECIMAL(8,2),                        -- 20日CCI

    -- ウィリアムズ%R
    williams_r_14 DECIMAL(5,2),                 -- 14日ウィリアムズ%R

    -- MFI（Money Flow Index）
    mfi_14 DECIMAL(5,2),                        -- 14日MFI

    -- Ultimate Oscillator
    ultimate_oscillator DECIMAL(5,2),           -- Ultimate Oscillator

    -- ==========================================
    -- 5. トレンド指標
    -- ==========================================
    -- ADX（Average Directional Index）
    adx_14 DECIMAL(5,2),                        -- 14日ADX
    plus_di_14 DECIMAL(5,2),                    -- +DI(14日)
    minus_di_14 DECIMAL(5,2),                   -- -DI(14日)

    -- パラボリックSAR
    parabolic_sar DECIMAL(10,2),                -- パラボリックSAR値
    sar_direction VARCHAR(10),                  -- 'LONG' or 'SHORT'

    -- 一目均衡表（Ichimoku）
    tenkan_sen DECIMAL(10,2),                   -- 転換線（9日）
    kijun_sen DECIMAL(10,2),                    -- 基準線（26日）
    senkou_span_a DECIMAL(10,2),                -- 先行スパンA
    senkou_span_b DECIMAL(10,2),                -- 先行スパンB
    chikou_span DECIMAL(10,2),                  -- 遅行スパン

    -- 雲の厚さ
    kumo_thickness DECIMAL(10,2),               -- |先行スパンA - 先行スパンB|
    is_above_kumo BOOLEAN,                      -- 価格が雲の上
    is_below_kumo BOOLEAN,                      -- 価格が雲の下

    -- ==========================================
    -- 6. ボラティリティ指標
    -- ==========================================
    -- ボリンジャーバンド
    bollinger_upper_2sigma DECIMAL(10,2),       -- 上限2σ
    bollinger_middle DECIMAL(10,2),             -- 中心線
    bollinger_lower_2sigma DECIMAL(10,2),       -- 下限2σ
    bollinger_width DECIMAL(10,4),              -- バンド幅
    bollinger_position DECIMAL(8,4),            -- バンド内の位置（%B）

    -- ATR（Average True Range）
    atr_14 DECIMAL(10,4),                       -- 14日ATR
    atr_20 DECIMAL(10,4),                       -- 20日ATR

    -- ヒストリカル・ボラティリティ
    volatility_10d DECIMAL(8,4),                -- 10日ボラティリティ
    volatility_20d DECIMAL(8,4),                -- 20日ボラティリティ
    volatility_60d DECIMAL(8,4),                -- 60日ボラティリティ

    -- ケルトナーチャネル
    keltner_upper DECIMAL(10,2),                -- ケルトナー上限
    keltner_middle DECIMAL(10,2),               -- ケルトナー中心
    keltner_lower DECIMAL(10,2),                -- ケルトナー下限

    -- ==========================================
    -- 7. 出来高系
    -- ==========================================
    -- 出来高移動平均
    volume_ma_5 BIGINT,                         -- 5日平均出来高
    volume_ma_10 BIGINT,                        -- 10日平均出来高
    volume_ma_20 BIGINT,                        -- 20日平均出来高
    volume_ma_60 BIGINT,                        -- 60日平均出来高

    -- 出来高比率
    volume_ratio_5 DECIMAL(8,4),                -- 当日出来高 / 5日平均
    volume_ratio_20 DECIMAL(8,4),               -- 当日出来高 / 20日平均

    -- 出来高変化率
    volume_change_1d DECIMAL(8,4),              -- 1日出来高変化率
    volume_change_5d DECIMAL(8,4),              -- 5日出来高変化率

    -- OBV（On-Balance Volume）
    obv BIGINT,                                 -- OBV
    obv_ma_20 BIGINT,                           -- 20日OBV移動平均

    -- VWAP（Volume Weighted Average Price）
    vwap DECIMAL(10,2),                         -- VWAP

    -- 出来高加重移動平均
    vwma_20 DECIMAL(10,2),                      -- 20日出来高加重移動平均

    -- CMF（Chaikin Money Flow）
    cmf_20 DECIMAL(8,4),                        -- 20日CMF

    -- ==========================================
    -- 8. 価格位置・高値安値
    -- ==========================================
    -- 高値・安値
    high_5d DECIMAL(10,2),                      -- 5日高値
    low_5d DECIMAL(10,2),                       -- 5日安値
    high_20d DECIMAL(10,2),                     -- 20日高値
    low_20d DECIMAL(10,2),                      -- 20日安値
    high_60d DECIMAL(10,2),                     -- 60日高値
    low_60d DECIMAL(10,2),                      -- 60日安値
    high_52w DECIMAL(10,2),                     -- 52週高値
    low_52w DECIMAL(10,2),                      -- 52週安値

    -- 高値・安値からの乖離率
    price_from_high_5d DECIMAL(8,4),            -- (価格 - 5日高値) / 5日高値
    price_from_low_5d DECIMAL(8,4),             -- (価格 - 5日安値) / 5日安値
    price_from_high_20d DECIMAL(8,4),           -- (価格 - 20日高値) / 20日高値
    price_from_low_20d DECIMAL(8,4),            -- (価格 - 20日安値) / 20日安値
    price_from_high_52w DECIMAL(8,4),           -- (価格 - 52週高値) / 52週高値
    price_from_low_52w DECIMAL(8,4),            -- (価格 - 52週安値) / 52週安値

    -- 価格の相対位置
    price_position_20d DECIMAL(5,4),            -- (価格 - 20日安値) / (20日高値 - 20日安値)
    price_position_52w DECIMAL(5,4),            -- (価格 - 52週安値) / (52週高値 - 52週安値)

    -- 新高値・新安値判定
    is_new_high_20d BOOLEAN,                    -- 20日新高値
    is_new_low_20d BOOLEAN,                     -- 20日新安値
    is_new_high_52w BOOLEAN,                    -- 52週新高値
    is_new_low_52w BOOLEAN,                     -- 52週新安値

    -- ==========================================
    -- 9. ローソク足パターン
    -- ==========================================
    -- 基本パターン
    is_doji BOOLEAN,                            -- 十字線
    is_hammer BOOLEAN,                          -- ハンマー
    is_inverted_hammer BOOLEAN,                 -- 逆ハンマー
    is_shooting_star BOOLEAN,                   -- 流れ星
    is_hanging_man BOOLEAN,                     -- 首吊り線

    -- 連続パターン
    consecutive_up_days INT,                    -- 連続陽線日数
    consecutive_down_days INT,                  -- 連続陰線日数

    -- 実体・ヒゲの比率
    body_size DECIMAL(8,4),                     -- (終値 - 始値) / 始値
    upper_shadow_ratio DECIMAL(8,4),            -- 上ヒゲの比率
    lower_shadow_ratio DECIMAL(8,4),            -- 下ヒゲの比率

    -- ==========================================
    -- 10. その他の指標
    -- ==========================================
    -- Awesome Oscillator
    awesome_oscillator DECIMAL(10,4),           -- Awesome Oscillator

    -- Aroon Indicator
    aroon_up DECIMAL(5,2),                      -- Aroon Up
    aroon_down DECIMAL(5,2),                    -- Aroon Down
    aroon_oscillator DECIMAL(5,2),              -- Aroon Oscillator

    -- ==========================================
    -- メタ情報
    -- ==========================================
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(stock_code, date)
);

CREATE INDEX idx_technical_indicators_code_date ON technical_indicators(stock_code, date DESC);
CREATE INDEX idx_technical_indicators_date ON technical_indicators(date DESC);
```

---

## Layer 3: Feature Store（機械学習特徴量）

### 10. ml_features（機械学習用特徴量）

```sql
CREATE TABLE ml_features (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    feature_version VARCHAR(10) NOT NULL,       -- v1, v2...（特徴量セットのバージョン）

    -- 特徴量をJSONB形式で保存
    features JSONB NOT NULL,

    -- 予測ターゲット（教師データ）
    target_return_1d DECIMAL(8,4),              -- 翌日騰落率
    target_return_5d DECIMAL(8,4),              -- 5日後騰落率
    target_return_1w DECIMAL(8,4),              -- 1週間後騰落率

    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(stock_code, date, feature_version)
);

CREATE INDEX idx_ml_features_code_date ON ml_features(stock_code, date DESC);
CREATE INDEX idx_ml_features_version ON ml_features(feature_version, date DESC);
CREATE INDEX idx_ml_features_features_gin ON ml_features USING GIN (features);
```

**features JSONBの構造例**:

```json
{
  "fundamental": {
    "per": 15.2,
    "pbr": 1.8,
    "roe": 12.5,
    "roa": 8.3,
    "debt_ratio": 0.45,
    "revenue_growth_yoy": 0.08,
    "profit_margin": 0.12,
    "dividend_yield": 2.5
  },
  "technical": {
    "ma_5": 1520.5,
    "ma_25": 1485.3,
    "rsi_14": 68.3,
    "macd": 12.5,
    "bollinger_position": 0.75,
    "return_5d": 0.025,
    "return_20d": 0.08,
    "volatility_20d": 0.015
  },
  "sentiment": {
    "margin_ratio": 1.25,
    "margin_buy_change_5d": 0.05,
    "short_selling_ratio": 15.3,
    "foreign_net_buy": 1500000000
  },
  "macro": {
    "topix_return_5d": 0.015,
    "sector_return_5d": 0.022,
    "market_volatility": 0.012
  }
}
```

---

## Layer 4: Prediction & Result（予測・結果）

### 11. rounds（ラウンド管理）

```sql
CREATE TABLE rounds (
    round_id VARCHAR(20) PRIMARY KEY,           -- 例: 2025-W10-BUY
    round_type VARCHAR(10) NOT NULL,            -- BUY / SELL
    start_date DATE NOT NULL,                   -- 開始日（月曜）
    end_date DATE NOT NULL,                     -- 終了日（金曜）
    status VARCHAR(20) NOT NULL,                -- ACTIVE / CLOSED
    model_version VARCHAR(20),                  -- 使用したモデルバージョン
    feature_version VARCHAR(10),                -- 使用した特徴量バージョン
    prediction_date DATE,                       -- 予測実施日
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rounds_type_date ON rounds(round_type, start_date DESC);
CREATE INDEX idx_rounds_status ON rounds(status);
```

### 12. round_recommendations（ラウンド推奨銘柄）

```sql
CREATE TABLE round_recommendations (
    id BIGSERIAL PRIMARY KEY,
    round_id VARCHAR(20) NOT NULL REFERENCES rounds(round_id),
    stock_code VARCHAR(10) NOT NULL,
    rank INT NOT NULL,                          -- 推奨順位（1〜N位）
    predicted_return DECIMAL(8,4),              -- 予測騰落率
    confidence_score DECIMAL(5,4),              -- 信頼度スコア（0〜1）
    reason_features JSONB,                      -- 推奨理由となった特徴量
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(round_id, stock_code)
);

CREATE INDEX idx_round_recommendations_round ON round_recommendations(round_id, rank);
CREATE INDEX idx_round_recommendations_code ON round_recommendations(stock_code, round_id);
```

### 13. round_results（ラウンド結果）

```sql
CREATE TABLE round_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id UUID NOT NULL REFERENCES rounds(id),
    stock_code VARCHAR(10) NOT NULL,

    -- 価格情報
    start_price DECIMAL(10,2),                  -- 開始時点の株価
    end_price DECIMAL(10,2),                    -- 終了時点の株価
    highest_price DECIMAL(10,2),                -- 期間中最高値
    lowest_price DECIMAL(10,2),                 -- 期間中最安値

    -- 実績
    actual_return DECIMAL(8,4),                 -- 実際の騰落率
    predicted_return DECIMAL(8,4),              -- 予測騰落率
    prediction_error DECIMAL(8,4),              -- 予測誤差
    prediction_hit BOOLEAN,                     -- 予測が当たったか

    -- 仮想損益
    entry_shares INT DEFAULT 100,               -- 仮想投資株数
    profit_loss DECIMAL(10,2),                  -- 損益金額
    profit_loss_rate DECIMAL(8,4),              -- 損益率

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(round_id, stock_code)
);

CREATE INDEX idx_round_results_round ON round_results(round_id);
CREATE INDEX idx_round_results_code ON round_results(stock_code);
```

### 14. daily_signals（デイリーシグナル）

```sql
CREATE TABLE daily_signals (
    id BIGSERIAL PRIMARY KEY,
    signal_date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL,           -- STRONG_BUY / STRONG_SELL
    predicted_return DECIMAL(8,4),              -- 予測騰落率
    confidence_score DECIMAL(5,4),              -- 信頼度スコア
    trigger_features JSONB,                     -- シグナル発生理由（特徴量）
    model_version VARCHAR(20),                  -- 使用したモデル

    -- 翌日検証用
    next_day_return DECIMAL(8,4),               -- 翌日の実際の騰落率
    signal_hit BOOLEAN,                         -- シグナルが当たったか

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(signal_date, stock_code, signal_type)
);

CREATE INDEX idx_daily_signals_date ON daily_signals(signal_date DESC);
CREATE INDEX idx_daily_signals_code ON daily_signals(stock_code, signal_date DESC);
CREATE INDEX idx_daily_signals_type ON daily_signals(signal_type, signal_date DESC);
```

---

## データ取得・更新フロー

### 毎営業日の更新フロー

```
【17:30〜18:00】J-Quants APIからデータ取得
├─ stock_prices_daily（株価四本値）
├─ stock_prices_am（前場四本値）
├─ margin_trading_daily（信用取引日次）
├─ short_selling_report（空売り残高）
├─ trading_breakdown（売買内訳）
└─ earnings_calendar（決算発表予定）※必要に応じて

【18:00〜18:30】計算済みデータ生成
├─ technical_indicators（テクニカル指標計算）
└─ ml_features（機械学習特徴量生成）

【18:30〜19:00】デイリーシグナル検出
└─ daily_signals（強い買い/売りシグナル）

【週末（金曜夜）】週次データ取得
├─ margin_trading_weekly（信用取引週末残高）
├─ investor_trading（投資部門別売買動向）
└─ short_selling_ratio（業種別空売り比率）

【週末（土曜）】ラウンド処理
├─ round_results（先週のラウンド結果検証）
└─ rounds + round_recommendations（来週のラウンド推奨生成）

【月次・四半期】財務データ更新
├─ financial_statements（決算発表時）
├─ dividend_info（配当発表時）
└─ stock_splits（株式分割発表時）

【適宜】マスタ更新
├─ stock_master（新規上場・廃止時）
└─ trading_calendar（年次更新）
```

---

## インデックス戦略

### 検索パフォーマンス最適化

各テーブルに以下のインデックスを設定：

- ✅ **銘柄コード + 日付降順** - 時系列データ取得の高速化
- ✅ **日付降順のみ** - 全銘柄の最新データ取得
- ✅ **ユニーク制約** - データ重複防止
- ✅ **GINインデックス（JSONB）** - 特徴量の柔軟な検索

---

## データ保持期間

| データ種別 | 保持期間 | 理由 |
|-----------|---------|------|
| **株価・財務** | 10年+ | 機械学習の長期バックテスト |
| **信用取引** | 10年+ | センチメント分析 |
| **テクニカル指標** | 10年+ | 特徴量として使用 |
| **ml_features** | 全期間 | モデル再学習時に使用 |
| **rounds/results** | 全期間 | パフォーマンス追跡 |
| **daily_signals** | 2年 | 短期シグナルは古いデータ不要 |

---

## 最終更新

- **日時**: 2026-07-21
- **更新者**: Claude Code
