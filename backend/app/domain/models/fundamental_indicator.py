"""ファンダメンタル指標関連モデル"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base, TimestampMixin


class FundamentalIndicator(TimestampMixin, Base):
    """ファンダメンタル指標（20項目）"""

    __tablename__ = "fundamental_indicators"

    # TimestampMixinから: id, created_at, updated_at（先頭に配置される）

    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, comment="銘柄コード")
    date: Mapped[date] = mapped_column(Date, nullable=False, comment="日付")

    # ==========================================
    # 1. バリュエーション指標（6項目）
    # ==========================================
    per: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="PER（株価収益率、実績）"
    )
    pbr: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="PBR（株価純資産倍率）"
    )
    psr: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="PSR（株価売上高倍率）"
    )
    pcfr: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="PCFR（株価キャッシュフロー倍率）"
    )
    forward_per_fy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="予想PER（当期）"
    )
    forward_per_nx: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="予想PER（翌期）"
    )

    # ==========================================
    # 2. 収益性指標（4項目）
    # ==========================================
    roe: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="ROE（自己資本利益率）"
    )
    roa: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="ROA（総資産利益率）"
    )
    operating_margin: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="営業利益率"
    )
    net_margin: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="純利益率"
    )

    # ==========================================
    # 3. 成長性指標（5項目、YoY）
    # ==========================================
    sales_growth_yoy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="売上高成長率（前年同期比）"
    )
    op_growth_yoy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="営業利益成長率（前年同期比）"
    )
    np_growth_yoy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="純利益成長率（前年同期比）"
    )
    eps_growth_yoy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="EPS成長率（前年同期比）"
    )
    cfo_growth_yoy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="営業CF成長率（前年同期比）"
    )

    # ==========================================
    # 4. 安全性指標（1項目）
    # ==========================================
    equity_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="自己資本比率"
    )

    # ==========================================
    # 5. 配当指標（4項目）
    # ==========================================
    dividend_yield: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="配当利回り（実績）"
    )
    payout_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), comment="配当性向（実績）"
    )
    forward_div_yield_fy: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="予想配当利回り（当期）"
    )
    forward_div_yield_nx: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), comment="予想配当利回り（翌期）"
    )

    # ==========================================
    # メタ情報
    # ==========================================
    calculated_at: Mapped[date] = mapped_column(Date, nullable=False, comment="計算日時")

    __table_args__ = (
        UniqueConstraint("stock_code", "date", name="uq_fundamental_indicators_code_date"),
        Index(
            "idx_fundamental_indicators_code_date",
            "stock_code",
            "date",
            postgresql_using="btree",
        ),
        Index("idx_fundamental_indicators_date", "date", postgresql_using="btree"),
        {"comment": "ファンダメンタル指標（20項目）"},
    )

    def __repr__(self) -> str:
        return (
            f"<FundamentalIndicator(code={self.stock_code}, date={self.date}, "
            f"per={self.per}, pbr={self.pbr}, roe={self.roe})>"
        )
