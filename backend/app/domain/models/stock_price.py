"""株価データ関連モデル"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class StockPriceDaily(TimestampMixin, Base):
    """株価日次データ"""

    __tablename__ = "stock_prices_daily"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="日付")

    # 四本値（調整前）
    open: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="始値")
    high: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="高値")
    low: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="安値")
    close: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="終値")
    volume: Mapped[int | None] = mapped_column(comment="出来高")
    turnover_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), comment="売買代金")

    # 調整済み四本値
    adjusted_open: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="調整後始値")
    adjusted_high: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="調整後高値")
    adjusted_low: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="調整後安値")
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), comment="調整後終値")
    adjusted_volume: Mapped[int | None] = mapped_column(comment="調整後出来高")
    adjustment_factor: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), comment="調整係数")

    # ストップ高/安フラグ
    is_upper_limit: Mapped[bool] = mapped_column(Boolean, default=False, comment="ストップ高フラグ")
    is_lower_limit: Mapped[bool] = mapped_column(Boolean, default=False, comment="ストップ安フラグ")

    # メタ情報
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="API取得日時")

    __table_args__ = (
        Index("idx_stock_prices_daily_code_date", "stock_code", "date", postgresql_using="btree"),
        Index("idx_stock_prices_daily_date", "date", postgresql_using="btree"),
        {"comment": "株価日次データ"},
    )

    def __repr__(self) -> str:
        return f"<StockPriceDaily(code={self.stock_code}, date={self.date}, close={self.close})>"
