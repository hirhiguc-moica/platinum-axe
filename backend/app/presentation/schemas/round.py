"""ラウンド関連スキーマ"""

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RoundSchema(BaseModel):
    """ラウンドスキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="UUID（主キー）")
    round_id: str = Field(..., description="ラウンドID（ビジネスキー、例: 2026-W30-BUY）")
    round_type: str = Field(..., description="ラウンドタイプ（BUY / SELL）")
    start_date: date = Field(..., description="開始日（月曜）")
    end_date: date = Field(..., description="終了日（金曜）")
    status: str = Field(..., description="ステータス（ACTIVE / CLOSED）")
    model_version: str | None = Field(None, description="使用したモデルバージョン")
    feature_version: str | None = Field(None, description="使用した特徴量バージョン")
    prediction_date: date | None = Field(None, description="予測実施日")


class StockInfoSchema(BaseModel):
    """銘柄情報スキーマ（推奨銘柄に含まれる）"""

    model_config = ConfigDict(from_attributes=True)

    stock_code: str = Field(..., description="銘柄コード")
    company_name: str = Field(..., description="会社名")
    sector_name: str | None = Field(None, description="業種名")
    market_name: str | None = Field(None, description="市場名（プライム/スタンダード等）")

    @model_validator(mode="before")
    @classmethod
    def extract_sector_and_market_info(cls, data: Any) -> dict[str, Any]:
        """Sector / Market relationshipから業種名・市場名を取得"""
        if hasattr(data, "__dict__"):
            return {
                "stock_code": data.stock_code,
                "company_name": data.company_name,
                "sector_name": data.sector.sector_name if hasattr(data, "sector") and data.sector else None,
                "market_name": data.market.market_short_name if hasattr(data, "market") and data.market else None,
            }
        return data


class RoundRecommendationSchema(BaseModel):
    """ラウンド推奨銘柄スキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="UUID（主キー）")
    round_id: UUID = Field(..., description="ラウンドID（UUID）")
    stock_code: str = Field(..., description="銘柄コード")
    rank: int = Field(..., description="推奨順位（1〜N位）")
    predicted_return: float | None = Field(None, description="予測騰落率")
    confidence_score: float | None = Field(None, description="信頼度スコア（0〜1）")
    reason_features: dict | None = Field(None, description="推奨理由となった特徴量")
    stock: StockInfoSchema | None = Field(None, description="銘柄情報")


class GetRoundsResponse(BaseModel):
    """ラウンド一覧レスポンス"""

    rounds: list[RoundSchema] = Field(..., description="ラウンドリスト")
    total: int = Field(..., description="総件数")


class GetRoundRecommendationsResponse(BaseModel):
    """ラウンド推奨銘柄レスポンス"""

    round: RoundSchema = Field(..., description="ラウンド情報")
    recommendations: list[RoundRecommendationSchema] = Field(..., description="推奨銘柄リスト")
