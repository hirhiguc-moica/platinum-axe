"""ラウンド関連モデル"""

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.stock import StockMaster


class Round(TimestampMixin, Base):
    """ラウンド管理"""

    __tablename__ = "rounds"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    round_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True, comment="ラウンドID（ビジネスキー）"
    )
    round_type: Mapped[str] = mapped_column(String(10), nullable=False, comment="BUY / SELL")
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment="開始日（月曜）")
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment="終了日（金曜）")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="ACTIVE / CLOSED"
    )
    model_version: Mapped[str | None] = mapped_column(
        String(20), comment="使用したモデルバージョン"
    )
    feature_version: Mapped[str | None] = mapped_column(
        String(10), comment="使用した特徴量バージョン"
    )
    prediction_date: Mapped[date | None] = mapped_column(Date, comment="予測実施日")

    # リレーション
    recommendations: Mapped[list["RoundRecommendation"]] = relationship(
        "RoundRecommendation", back_populates="round", cascade="all, delete-orphan"
    )

    __table_args__ = ({"comment": "ラウンド管理"},)

    def __repr__(self) -> str:
        return f"<Round(id={self.round_id}, type={self.round_type}, status={self.status})>"


class RoundRecommendation(TimestampMixin, Base):
    """ラウンド推奨銘柄"""

    __tablename__ = "round_recommendations"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    round_id: Mapped[UUID] = mapped_column(
        ForeignKey("rounds.id"), nullable=False, index=True, comment="ラウンドID（UUID）"
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")
    rank: Mapped[int] = mapped_column(Integer, nullable=False, comment="推奨順位（1〜N位）")
    predicted_return: Mapped[float | None] = mapped_column(
        Numeric(8, 4), comment="予測騰落率"
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Numeric(5, 4), comment="信頼度スコア（0〜1）"
    )
    reason_features: Mapped[dict | None] = mapped_column(
        JSONB, comment="推奨理由となった特徴量"
    )

    # リレーション
    round: Mapped["Round"] = relationship("Round", back_populates="recommendations")
    stock: Mapped["StockMaster"] = relationship(
        "StockMaster",
        primaryjoin="foreign(RoundRecommendation.stock_code) == StockMaster.stock_code",
        viewonly=True,
        lazy="selectin",
    )

    __table_args__ = ({"comment": "ラウンド推奨銘柄"},)

    def __repr__(self) -> str:
        return (
            f"<RoundRecommendation(round={self.round_id}, "
            f"code={self.stock_code}, rank={self.rank})>"
        )
