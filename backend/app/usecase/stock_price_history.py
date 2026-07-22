"""株価履歴取得ユースケース"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.stock_price_repository import StockPriceRepository


class GetStockPriceHistoryUseCase:
    """株価履歴取得ユースケース（ページング対応）"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stock_price_repo = StockPriceRepository(session)

    async def execute(
        self,
        stock_code: str,
        page: int = 1,
        limit: int = 200,
    ) -> dict:
        """株価履歴取得

        Args:
            stock_code: 銘柄コード
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数

        Returns:
            株価履歴データ（ページング情報付き）
        """
        offset = (page - 1) * limit

        # データ取得
        prices = await self.stock_price_repo.find_by_stock_code(
            stock_code=stock_code,
            limit=limit,
            offset=offset,
        )

        # 総件数取得
        total = await self.stock_price_repo.count_by_stock_code(stock_code)

        # レスポンス整形
        items = [
            {
                "date": price.date,
                "open": float(price.open) if price.open else None,
                "high": float(price.high) if price.high else None,
                "low": float(price.low) if price.low else None,
                "close": float(price.close) if price.close else None,
                "volume": price.volume,
                "adjusted_close": float(price.adjusted_close) if price.adjusted_close else None,
            }
            for price in prices
        ]

        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        }
