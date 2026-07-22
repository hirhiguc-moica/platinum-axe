"""テクニカル指標履歴取得ユースケース"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.technical_indicator_repository import (
    TechnicalIndicatorRepository,
)


class GetStockTechnicalIndicatorsUseCase:
    """テクニカル指標履歴取得ユースケース（ページング対応）"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.technical_repo = TechnicalIndicatorRepository(session)

    async def execute(
        self,
        stock_code: str,
        page: int = 1,
        limit: int = 200,
    ) -> dict:
        """テクニカル指標履歴取得

        Args:
            stock_code: 銘柄コード
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数

        Returns:
            テクニカル指標履歴データ（ページング情報付き）
        """
        offset = (page - 1) * limit

        # データ取得
        indicators = await self.technical_repo.find_by_stock_code(
            stock_code=stock_code,
            limit=limit,
            offset=offset,
        )

        # 総件数取得
        total = await self.technical_repo.count_by_stock_code(stock_code)

        # レスポンス整形（主要指標のみ抽出）
        items = []
        for ind in indicators:
            item = {
                "date": ind.date,
                # 移動平均線
                "ma_5": float(ind.ma_5) if ind.ma_5 else None,
                "ma_25": float(ind.ma_25) if ind.ma_25 else None,
                "ma_75": float(ind.ma_75) if ind.ma_75 else None,
                "ema_12": float(ind.ema_12) if ind.ema_12 else None,
                "ema_26": float(ind.ema_26) if ind.ema_26 else None,
                # モメンタム
                "rsi_14": float(ind.rsi_14) if ind.rsi_14 else None,
                "macd": float(ind.macd) if ind.macd else None,
                "macd_signal": float(ind.macd_signal) if ind.macd_signal else None,
                "macd_histogram": float(ind.macd_histogram) if ind.macd_histogram else None,
                # ボラティリティ
                "bollinger_upper_2sigma": float(ind.bollinger_upper_2sigma) if ind.bollinger_upper_2sigma else None,
                "bollinger_middle": float(ind.bollinger_middle)
                if ind.bollinger_middle
                else None,
                "bollinger_lower_2sigma": float(ind.bollinger_lower_2sigma) if ind.bollinger_lower_2sigma else None,
                "atr_14": float(ind.atr_14) if ind.atr_14 else None,
                # 出来高
                "volume_ma_20": float(ind.volume_ma_20) if ind.volume_ma_20 else None,
                "obv": float(ind.obv) if ind.obv else None,
                # その他
                "adx_14": float(ind.adx_14) if ind.adx_14 else None,
            }
            items.append(item)

        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        }
