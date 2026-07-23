"""テクニカル指標リポジトリ"""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import TechnicalIndicator


class TechnicalIndicatorRepository:
    """テクニカル指標リポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_stock_code(
        self,
        stock_code: str,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[TechnicalIndicator]:
        """銘柄コードでテクニカル指標を取得（ページング対応）

        Args:
            stock_code: 銘柄コード
            limit: 取得件数
            offset: オフセット

        Returns:
            テクニカル指標リスト（新しい順）
        """
        stmt = (
            select(TechnicalIndicator)
            .where(TechnicalIndicator.stock_code == stock_code)
            .order_by(TechnicalIndicator.date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_stock_code(self, stock_code: str) -> int:
        """銘柄コードでテクニカル指標件数を取得

        Args:
            stock_code: 銘柄コード

        Returns:
            件数
        """
        stmt = (
            select(func.count())
            .select_from(TechnicalIndicator)
            .where(TechnicalIndicator.stock_code == stock_code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_latest_by_stock_code(
        self,
        stock_code: str,
    ) -> TechnicalIndicator | None:
        """銘柄コードで最新のテクニカル指標を取得

        Args:
            stock_code: 銘柄コード

        Returns:
            最新のテクニカル指標（存在しない場合はNone）
        """
        stmt = (
            select(TechnicalIndicator)
            .where(TechnicalIndicator.stock_code == stock_code)
            .order_by(TechnicalIndicator.date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_date_range(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[TechnicalIndicator]:
        """期間指定でテクニカル指標を取得

        Args:
            stock_code: 銘柄コード
            start_date: 開始日
            end_date: 終了日

        Returns:
            テクニカル指標リスト（古い順）
        """
        stmt = (
            select(TechnicalIndicator)
            .where(
                TechnicalIndicator.stock_code == stock_code,
                TechnicalIndicator.date >= start_date,
                TechnicalIndicator.date <= end_date,
            )
            .order_by(TechnicalIndicator.date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
