"""銘柄関連モデル"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.market import Market
    from app.domain.models.sector import Sector
    from app.domain.models.sector17 import Sector17


class StockMaster(TimestampMixin, Base):
    """銘柄マスタ"""

    __tablename__ = "stock_master"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    stock_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True, comment="銘柄コード（ビジネスキー）"
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, comment="会社名")
    company_name_en: Mapped[str | None] = mapped_column(String(255), comment="英語名")
    sector_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("sectors.sector_code"),
        index=True,
        comment="業種コード（33業種分類）",
    )
    sector17_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("sector17s.sector17_code"),
        index=True,
        comment="17業種コード",
    )
    market_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("markets.market_code"),
        index=True,
        comment="市場区分コード",
    )
    scale_category: Mapped[str | None] = mapped_column(
        String(50), comment="規模区分（TOPIX分類: TOPIX Core30, Large70, Mid400, Small 1/2）"
    )
    margin_code: Mapped[str | None] = mapped_column(
        String(10), comment="信用区分コード（1: 信用 / 2: 貸借 / 3: その他）"
    )
    info_date: Mapped[date | None] = mapped_column(
        Date, index=True, comment="情報適用年月日（APIのDateフィールド、更新判断に使用）"
    )
    listing_date: Mapped[date | None] = mapped_column(Date, comment="上場日")
    delisting_date: Mapped[date | None] = mapped_column(Date, comment="上場廃止日")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, comment="上場中フラグ"
    )
    market_cap: Mapped[float | None] = mapped_column(Numeric(15, 2), comment="時価総額（最新）")
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="API取得日時")

    # 指数組入銘柄フラグ
    is_nikkei225: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="日経225組入銘柄フラグ"
    )
    is_topix: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True, comment="TOPIX組入銘柄フラグ"
    )
    is_topix_core30: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="TOPIX Core30組入銘柄フラグ"
    )
    is_jpx400: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="JPX日経400組入銘柄フラグ"
    )

    # リレーション
    sector: Mapped["Sector"] = relationship(
        "Sector",
        foreign_keys=[sector_code],
        primaryjoin="foreign(StockMaster.sector_code) == Sector.sector_code",
        viewonly=True,
        lazy="selectin",
    )
    sector17: Mapped["Sector17"] = relationship(
        "Sector17",
        foreign_keys=[sector17_code],
        primaryjoin="foreign(StockMaster.sector17_code) == Sector17.sector17_code",
        viewonly=True,
        lazy="selectin",
    )
    market: Mapped["Market"] = relationship(
        "Market",
        foreign_keys=[market_code],
        primaryjoin="foreign(StockMaster.market_code) == Market.market_code",
        viewonly=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StockMaster(code={self.stock_code}, name={self.company_name})>"
