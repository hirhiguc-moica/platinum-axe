"""17業種マスタモデル"""

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class Sector17(TimestampMixin, Base):
    """17業種マスタ（JPX分類）"""

    __tablename__ = "sector17s"

    # TimestampMixinから: id, created_at, updated_at

    sector17_code: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True, comment="17業種コード（J-Quants API）"
    )
    sector17_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="17業種名")

    __table_args__ = (
        UniqueConstraint("sector17_code", name="uq_sector17s_sector17_code"),
        {"comment": "17業種マスタ（JPX分類）"},
    )

    def __repr__(self) -> str:
        return f"<Sector17(code={self.sector17_code}, name={self.sector17_name})>"
