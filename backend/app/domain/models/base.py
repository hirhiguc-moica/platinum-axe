"""SQLAlchemy Base Model"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """全てのモデルの基底クラス（抽象クラス）"""

    pass


class TimestampMixin:
    """
    タイムスタンプMixin

    全テーブル共通のマジックカラム：
    - id: UUID主キー
    - created_at: 作成日時
    - updated_at: 更新日時

    NOTE: 各モデルで先頭に配置すること
    """

    @declared_attr
    def id(cls) -> Mapped[UUID]:
        return mapped_column(
            primary_key=True,
            default=uuid4,
            server_default=text("gen_random_uuid()"),
            comment="主キー（UUID）",
        )

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            default=datetime.now,
            server_default=text("CURRENT_TIMESTAMP"),
            comment="作成日時",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            default=datetime.now,
            onupdate=datetime.now,
            server_default=text("CURRENT_TIMESTAMP"),
            comment="更新日時",
        )
