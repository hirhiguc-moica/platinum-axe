"""ラウンド結果関連モデル"""

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.round import Round


class RoundResult(TimestampMixin, Base):
    """ラウンド結果"""

    __tablename__ = "round_results"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    round_id: Mapped[UUID] = mapped_column(
        ForeignKey("rounds.id"), nullable=False, index=True, comment="ラウンドID（UUID）"
    )
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")

    # 価格情報
    start_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="開始時点の株価"
    )
    end_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="終了時点の株価")
    highest_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="期間中最高値"
    )
    lowest_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="期間中最安値")

    # 実績
    actual_return: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="実際の騰落率"
    )
    predicted_return: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="予測騰落率"
    )
    prediction_error: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="予測誤差"
    )
    prediction_hit: Mapped[bool | None] = mapped_column(
        Boolean, comment="予測が当たったか"
    )

    # 仮想損益
    entry_shares: Mapped[int] = mapped_column(
        Integer, default=100, comment="仮想投資株数"
    )
    profit_loss: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="損益金額")
    profit_loss_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4), comment="損益率"
    )

    # リレーション
    round: Mapped["Round"] = relationship("Round", back_populates="results")

    __table_args__ = (
        Index("idx_round_results_round", "round_id", postgresql_using="btree"),
        Index("idx_round_results_code", "stock_code", postgresql_using="btree"),
        {"comment": "ラウンド結果"},
    )

    def __repr__(self) -> str:
        return (
            f"<RoundResult(round={self.round_id}, code={self.stock_code}, "
            f"actual_return={self.actual_return})>"
        )
