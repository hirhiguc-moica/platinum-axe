"""銘柄関連リポジトリ"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import StockMaster


class StockRepository:
    """銘柄リポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self, query: str, limit: int = 10, offset: int = 0
    ) -> list[StockMaster]:
        """
        銘柄検索（銘柄コード・会社名の部分一致）

        Args:
            query: 検索キーワード
            limit: 取得件数
            offset: オフセット

        Returns:
            銘柄リスト
        """
        # 銘柄コードまたは会社名の部分一致検索
        stmt = (
            select(StockMaster)
            .where(
                or_(
                    StockMaster.stock_code.ilike(f"%{query}%"),
                    StockMaster.company_name.ilike(f"%{query}%"),
                )
            )
            .options(
                selectinload(StockMaster.sector), selectinload(StockMaster.market)
            )
            .order_by(StockMaster.stock_code)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_stock_code(self, stock_code: str) -> StockMaster | None:
        """
        銘柄コード検索

        Args:
            stock_code: 銘柄コード

        Returns:
            銘柄（存在しない場合はNone）
        """
        stmt = (
            select(StockMaster)
            .where(StockMaster.stock_code == stock_code)
            .options(
                selectinload(StockMaster.sector), selectinload(StockMaster.market)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
