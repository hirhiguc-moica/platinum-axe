"""セクター指数データ関連モデル"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class SectorIndexDaily(TimestampMixin, Base):
    """セクター指数日次データ

    全38指数を保存（TOPIX関連9 + 市場別4 + TOPIX-17業種別17 + REIT 1）
    Phase 1では18指数（TOPIX + TOPIX-17業種別17）を機械学習に使用
    """

    __tablename__ = "sector_indices_daily"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    index_code: Mapped[str] = mapped_column(String(4), nullable=False, comment="指数コード（例: 0000, 0080）")
    index_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="指数名（例: TOPIX, 食品）")
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="日付")

    # 生データ（J-Quants APIから取得、機械学習用、FE表示不可）
    open: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="始値")
    high: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="高値")
    low: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="安値")
    close: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="終値")

    # 計算済み騰落率（FE表示可）
    change_rate_1d: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="前日比騰落率（%）")
    change_rate_5d: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="5日前比騰落率（%）")
    change_rate_20d: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="20日前比騰落率（%）")
    change_rate_60d: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), comment="60日前比騰落率（%）")

    __table_args__ = (
        UniqueConstraint("index_code", "date", name="uq_sector_indices_daily_code_date"),
        Index("ix_sector_indices_daily_index_code", "index_code"),
        Index("ix_sector_indices_daily_date", "date"),
        Index("ix_sector_indices_daily_code_date", "index_code", "date"),
        {"comment": "セクター指数日次データ（全38指数、Phase 1では18指数を機械学習に使用）"},
    )

    def __repr__(self) -> str:
        return f"<SectorIndexDaily(code={self.index_code}, name={self.index_name}, date={self.date}, close={self.close})>"
