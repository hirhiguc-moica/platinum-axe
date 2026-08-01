"""信用取引残高データ関連モデル"""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class MarginTradingBalance(TimestampMixin, Base):
    """信用取引週末残高データ

    J-Quants API /v2/markets/margin-interest から取得
    週末（通常金曜日）時点での信用取引残高
    """

    __tablename__ = "margin_trading_balance"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    stock_code: Mapped[str] = mapped_column(
        String(10), ForeignKey("stock_master.stock_code"), nullable=False, comment="銘柄コード"
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="週末日付（通常金曜日）")

    # 生データ（J-Quants APIレスポンス、DB内部のみ保存、Web表示禁止）
    short_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="売合計信用残高（株数）")
    long_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="買合計信用残高（株数）")
    short_neg_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="一般信用取引売残高（株数）")
    long_neg_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="一般信用取引買残高（株数）")
    short_std_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="制度信用取引売残高（株数）")
    long_std_vol: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="制度信用取引買残高（株数）")
    iss_type: Mapped[str] = mapped_column(String(1), nullable=False, comment="銘柄区分（1:信用、2:貸借、3:その他）")

    # 計算済み指標（Web/API表示可、機械学習特徴量）
    margin_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="信用倍率（買い残 ÷ 売り残）"
    )
    long_vol_change: Mapped[int | None] = mapped_column(BigInteger, comment="買い残前週比増減（株数）")
    short_vol_change: Mapped[int | None] = mapped_column(BigInteger, comment="売り残前週比増減（株数）")
    long_vol_change_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="買い残前週比増減率（%）"
    )
    short_vol_change_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="売り残前週比増減率（%）"
    )

    __table_args__ = (
        UniqueConstraint("stock_code", "date", name="uq_margin_trading_balance_code_date"),
        Index("ix_margin_trading_balance_stock_code", "stock_code"),
        Index("ix_margin_trading_balance_date", "date"),
        Index("ix_margin_trading_balance_code_date", "stock_code", "date"),
        {"comment": "信用取引週末残高データ（週次、全銘柄）"},
    )

    def __repr__(self) -> str:
        return f"<MarginTradingBalance(code={self.stock_code}, date={self.date}, ratio={self.margin_ratio})>"
