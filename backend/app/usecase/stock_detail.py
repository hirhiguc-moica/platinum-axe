"""銘柄詳細取得ユースケース"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import StockMaster
from app.infrastructure.repositories.stock_price_repository import StockPriceRepository


class GetStockDetailUseCase:
    """銘柄詳細取得ユースケース

    銘柄基本情報 + 最新株価を取得
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stock_price_repo = StockPriceRepository(session)

    async def execute(self, stock_code: str) -> dict | None:
        """銘柄詳細取得

        Args:
            stock_code: 銘柄コード

        Returns:
            銘柄詳細情報（存在しない場合はNone）
        """
        # 銘柄マスタ取得
        stmt = (
            select(StockMaster)
            .options(
                selectinload(StockMaster.sector),
                selectinload(StockMaster.market),
            )
            .where(StockMaster.stock_code == stock_code)
        )
        result = await self.session.execute(stmt)
        stock_master = result.scalar_one_or_none()

        if not stock_master:
            return None

        # 最新株価取得
        latest_price = await self.stock_price_repo.find_latest_by_stock_code(stock_code)

        return {
            "stock_code": stock_master.stock_code,
            "company_name": stock_master.company_name,
            "sector_code": stock_master.sector_code,
            "sector_name": stock_master.sector.sector_name if stock_master.sector else None,
            "market_code": stock_master.market_code,
            "market_name": stock_master.market.market_name if stock_master.market else None,
            "is_nikkei225": stock_master.is_nikkei225,
            "is_topix": stock_master.is_topix,
            "is_topix_core30": stock_master.is_topix_core30,
            "is_jpx400": stock_master.is_jpx400,
            "latest_price": {
                "date": latest_price.date,
                "open": float(latest_price.open) if latest_price.open else None,
                "high": float(latest_price.high) if latest_price.high else None,
                "low": float(latest_price.low) if latest_price.low else None,
                "close": float(latest_price.close) if latest_price.close else None,
                "volume": latest_price.volume,
            }
            if latest_price
            else None,
        }
