"""業種マスタモデル"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class Sector(TimestampMixin, Base):
    """業種マスタ"""

    __tablename__ = "sectors"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    sector_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True, comment="業種コード（33業種分類）"
    )
    sector_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="業種名")
    sector_name_en: Mapped[str | None] = mapped_column(String(100), comment="業種名（英語）")

    __table_args__ = ({"comment": "業種マスタ（33業種分類）"},)

    def __repr__(self) -> str:
        return f"<Sector(code={self.sector_code}, name={self.sector_name})>"
