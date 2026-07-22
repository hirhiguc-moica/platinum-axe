"""株価データリポジトリ"""

from datetime import date
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import StockPriceDaily


class StockPriceRepository:
    """株価データリポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_stock_code(
        self,
        stock_code: str,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[StockPriceDaily]:
        """銘柄コードで株価データを取得（ページング対応）

        Args:
            stock_code: 銘柄コード
            limit: 取得件数
            offset: オフセット

        Returns:
            株価データリスト（新しい順）
        """
        stmt = (
            select(StockPriceDaily)
            .where(StockPriceDaily.stock_code == stock_code)
            .order_by(StockPriceDaily.date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_stock_code(self, stock_code: str) -> int:
        """銘柄コードで株価データ件数を取得

        Args:
            stock_code: 銘柄コード

        Returns:
            件数
        """
        stmt = select(func.count()).select_from(StockPriceDaily).where(
            StockPriceDaily.stock_code == stock_code
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_latest_by_stock_code(
        self,
        stock_code: str,
    ) -> StockPriceDaily | None:
        """銘柄コードで最新の株価データを取得

        Args:
            stock_code: 銘柄コード

        Returns:
            最新の株価データ（存在しない場合はNone）
        """
        stmt = (
            select(StockPriceDaily)
            .where(StockPriceDaily.stock_code == stock_code)
            .order_by(StockPriceDaily.date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_date_range(
        self,
        stock_code: str,
        start_date: date,
        end_date: date,
    ) -> Sequence[StockPriceDaily]:
        """期間指定で株価データを取得

        Args:
            stock_code: 銘柄コード
            start_date: 開始日
            end_date: 終了日

        Returns:
            株価データリスト（古い順）
        """
        stmt = (
            select(StockPriceDaily)
            .where(
                StockPriceDaily.stock_code == stock_code,
                StockPriceDaily.date >= start_date,
                StockPriceDaily.date <= end_date,
            )
            .order_by(StockPriceDaily.date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
