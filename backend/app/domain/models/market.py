"""市場マスタモデル"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class Market(TimestampMixin, Base):
    """市場マスタ（プライム/スタンダード/グロース等）

    東証の市場区分をマスタ管理する。
    2022年4月の市場再編後の区分（プライム/スタンダード/グロース）を基本とする。

    Attributes:
        market_code: J-Quants APIの市場コード（例: 0111=プライム内国株式）
        market_name: 市場名（例: プライム（内国株式））
        market_short_name: 短縮名（例: プライム）
        market_abbreviation: 略号（例: PR）
        market_category: カテゴリ（PRIME/STANDARD/GROWTH）
        market_type: 市場種別（内国株式/外国株式）
        sort_order: 表示順（1=プライム, 2=スタンダード, 3=グロース）
    """

    __tablename__ = "markets"
    __table_args__ = {"comment": "市場マスタ（プライム/スタンダード/グロース等）"}

    market_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True, comment="市場コード（J-Quants API）"
    )
    market_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="市場名")
    market_short_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="短縮名")
    market_abbreviation: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="略号（PR/ST/GR等）"
    )
    market_category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="カテゴリ（PRIME/STANDARD/GROWTH）"
    )
    market_type: Mapped[str | None] = mapped_column(
        String(50), comment="市場種別（内国株式/外国株式）"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, comment="表示順")
