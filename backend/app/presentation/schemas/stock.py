"""銘柄関連スキーマ"""

from datetime import date as Date

from pydantic import BaseModel, Field


class PaginationSchema(BaseModel):
    """ページング情報"""

    page: int = Field(..., description="現在のページ番号")
    limit: int = Field(..., description="1ページあたりの件数")
    total: int = Field(..., description="総件数")
    total_pages: int = Field(..., description="総ページ数")


class LatestPriceSchema(BaseModel):
    """最新株価スキーマ"""

    date: Date = Field(..., description="日付")
    open: float | None = Field(None, description="始値")
    high: float | None = Field(None, description="高値")
    low: float | None = Field(None, description="安値")
    close: float | None = Field(None, description="終値")
    volume: int | None = Field(None, description="出来高")


class StockSearchItemSchema(BaseModel):
    """銘柄検索結果アイテムスキーマ"""

    stock_code: str = Field(..., description="銘柄コード")
    company_name: str = Field(..., description="会社名")
    sector_code: str | None = Field(None, description="業種コード")
    sector_name: str | None = Field(None, description="業種名")
    market_code: str | None = Field(None, description="市場コード")
    market_name: str | None = Field(None, description="市場名")
    market_abbreviation: str | None = Field(None, description="市場略称（PR/ST/GR）")
    is_nikkei225: bool = Field(..., description="日経225構成銘柄")
    is_topix: bool = Field(..., description="TOPIX構成銘柄")


class StockSearchResponse(BaseModel):
    """銘柄検索レスポンス"""

    stocks: list[StockSearchItemSchema] = Field(..., description="検索結果")


class StockDetailResponse(BaseModel):
    """銘柄詳細レスポンス"""

    stock_code: str = Field(..., description="銘柄コード")
    company_name: str = Field(..., description="会社名")
    sector_code: str | None = Field(None, description="業種コード")
    sector_name: str | None = Field(None, description="業種名")
    market_code: str | None = Field(None, description="市場コード")
    market_name: str | None = Field(None, description="市場名")
    is_nikkei225: bool = Field(..., description="日経225構成銘柄")
    is_topix: bool = Field(..., description="TOPIX構成銘柄")
    is_topix_core30: bool = Field(..., description="TOPIX Core30構成銘柄")
    is_jpx400: bool = Field(..., description="JPX400構成銘柄")
    latest_price: LatestPriceSchema | None = Field(None, description="最新株価")


class StockPriceItemSchema(BaseModel):
    """株価履歴アイテムスキーマ"""

    date: Date = Field(..., description="日付")
    open: float | None = Field(None, description="始値")
    high: float | None = Field(None, description="高値")
    low: float | None = Field(None, description="安値")
    close: float | None = Field(None, description="終値")
    volume: int | None = Field(None, description="出来高")
    adjusted_close: float | None = Field(None, description="調整後終値")


class StockPriceHistoryResponse(BaseModel):
    """株価履歴レスポンス"""

    items: list[StockPriceItemSchema] = Field(..., description="株価データリスト")
    pagination: PaginationSchema = Field(..., description="ページング情報")


class TechnicalIndicatorItemSchema(BaseModel):
    """テクニカル指標アイテムスキーマ（主要指標のみ）"""

    date: Date = Field(..., description="日付")
    # 移動平均線
    ma_5: float | None = Field(None, description="5日移動平均")
    ma_25: float | None = Field(None, description="25日移動平均")
    ma_75: float | None = Field(None, description="75日移動平均")
    ema_12: float | None = Field(None, description="12日指数移動平均")
    ema_26: float | None = Field(None, description="26日指数移動平均")
    # モメンタム
    rsi_14: float | None = Field(None, description="14日RSI")
    macd: float | None = Field(None, description="MACD")
    macd_signal: float | None = Field(None, description="MACDシグナル")
    macd_histogram: float | None = Field(None, description="MACDヒストグラム")
    # ボラティリティ
    bollinger_upper_2sigma: float | None = Field(None, description="ボリンジャーバンド上限（2σ）")
    bollinger_middle: float | None = Field(None, description="ボリンジャーバンド中央線")
    bollinger_lower_2sigma: float | None = Field(None, description="ボリンジャーバンド下限（2σ）")
    atr_14: float | None = Field(None, description="14日ATR")
    # 出来高
    volume_ma_20: float | None = Field(None, description="20日出来高移動平均")
    obv: float | None = Field(None, description="OBV（On-Balance Volume）")
    # その他
    adx_14: float | None = Field(None, description="14日ADX")


class TechnicalIndicatorResponse(BaseModel):
    """テクニカル指標履歴レスポンス"""

    items: list[TechnicalIndicatorItemSchema] = Field(..., description="テクニカル指標データリスト")
    pagination: PaginationSchema = Field(..., description="ページング情報")


class RecommendationHistoryItemSchema(BaseModel):
    """推奨履歴アイテムスキーマ"""

    round_id: str = Field(..., description="ラウンドID（ビジネスキー）")
    round_type: str = Field(..., description="ラウンドタイプ（BUY / SELL）")
    start_date: Date = Field(..., description="開始日")
    end_date: Date = Field(..., description="終了日")
    status: str = Field(..., description="ステータス")
    rank: int = Field(..., description="推奨順位")
    predicted_return: float | None = Field(None, description="予測騰落率")
    confidence_score: float | None = Field(None, description="信頼度スコア")
    # 実績データ
    actual_return: float | None = Field(None, description="実際の騰落率")
    prediction_hit: bool | None = Field(None, description="予測が当たったか")
    start_price: float | None = Field(None, description="開始時点の株価")
    end_price: float | None = Field(None, description="終了時点の株価")


class RecommendationHistoryResponse(BaseModel):
    """推奨履歴レスポンス"""

    items: list[RecommendationHistoryItemSchema] = Field(..., description="推奨履歴データリスト")
    pagination: PaginationSchema = Field(..., description="ページング情報")
