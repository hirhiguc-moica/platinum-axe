"""銘柄検索ユースケース"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.stock_repository import StockRepository


class SearchStocksUseCase:
    """銘柄検索ユースケース

    銘柄コード・会社名の部分一致検索
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stock_repo = StockRepository(session)

    async def execute(self, query: str, limit: int = 10) -> list[dict]:
        """銘柄検索

        Args:
            query: 検索キーワード（銘柄コードまたは会社名）
            limit: 取得件数（デフォルト10件）

        Returns:
            銘柄リスト
        """
        if not query or len(query) < 1:
            return []

        stocks = await self.stock_repo.search(query=query, limit=limit)

        return [
            {
                "stock_code": stock.stock_code,
                "company_name": stock.company_name,
                "sector_code": stock.sector_code,
                "sector_name": stock.sector.sector_name if stock.sector else None,
                "market_code": stock.market_code,
                "market_name": stock.market.market_name if stock.market else None,
                "market_abbreviation": stock.market.market_abbreviation if stock.market else None,
                "is_nikkei225": stock.is_nikkei225,
                "is_topix": stock.is_topix,
            }
            for stock in stocks
        ]
