"""銘柄推奨履歴取得ユースケース"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Round, RoundRecommendation, RoundResult


class GetStockRecommendationHistoryUseCase:
    """銘柄推奨履歴取得ユースケース（ページング対応）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def execute(
        self,
        stock_code: str,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """銘柄推奨履歴取得

        Args:
            stock_code: 銘柄コード
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数

        Returns:
            推奨履歴データ（ページング情報付き）
        """
        offset = (page - 1) * limit

        # データ取得（RoundResultをLEFT JOIN）
        stmt = (
            select(RoundRecommendation, RoundResult)
            .options(selectinload(RoundRecommendation.round))
            .where(RoundRecommendation.stock_code == stock_code)
            .join(Round, RoundRecommendation.round_id == Round.id)
            .outerjoin(
                RoundResult,
                (RoundResult.round_id == RoundRecommendation.round_id)
                & (RoundResult.stock_code == RoundRecommendation.stock_code),
            )
            .order_by(Round.start_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        # 総件数取得
        count_stmt = (
            select(func.count())
            .select_from(RoundRecommendation)
            .where(RoundRecommendation.stock_code == stock_code)
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # レスポンス整形
        items = []
        for rec, result_data in rows:
            item = {
                "round_id": rec.round.round_id,
                "round_type": rec.round.round_type,
                "start_date": rec.round.start_date,
                "end_date": rec.round.end_date,
                "status": rec.round.status,
                "rank": rec.rank,
                "predicted_return": float(rec.predicted_return) if rec.predicted_return else None,
                "confidence_score": float(rec.confidence_score) if rec.confidence_score else None,
                # 実績データ（RoundResultが存在する場合のみ）
                "actual_return": (
                    float(result_data.actual_return)
                    if result_data and result_data.actual_return
                    else None
                ),
                "prediction_hit": result_data.prediction_hit if result_data else None,
                "start_price": float(result_data.start_price)
                if result_data and result_data.start_price
                else None,
                "end_price": float(result_data.end_price)
                if result_data and result_data.end_price
                else None,
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
