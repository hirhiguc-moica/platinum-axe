"""ラウンド結果リポジトリ"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.round import Round
from app.domain.models.round_result import RoundResult
from app.domain.models.stock import StockMaster


class RoundResultRepository:
    """ラウンド結果リポジトリ"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_round_uuid(self, round_uuid: UUID) -> list[RoundResult]:
        """ラウンドUUIDから結果一覧を取得"""
        stmt = select(RoundResult).where(RoundResult.round_id == round_uuid)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_closed_rounds(self) -> dict[str, Round | None]:
        """直近のクローズ済みラウンド（BUY/SELL）を取得"""
        # BUYの直近
        buy_stmt = (
            select(Round)
            .where(Round.round_type == "BUY", Round.status == "CLOSED")
            .order_by(Round.start_date.desc())
            .limit(1)
        )
        buy_result = await self.session.execute(buy_stmt)
        buy_round = buy_result.scalar_one_or_none()

        # SELLの直近
        sell_stmt = (
            select(Round)
            .where(Round.round_type == "SELL", Round.status == "CLOSED")
            .order_by(Round.start_date.desc())
            .limit(1)
        )
        sell_result = await self.session.execute(sell_stmt)
        sell_round = sell_result.scalar_one_or_none()

        return {"buy": buy_round, "sell": sell_round}

    async def get_round_performance(
        self, round_uuid: UUID, index_filter: str = "all"
    ) -> dict[str, float | int]:
        """ラウンドのパフォーマンス統計を計算

        Args:
            round_uuid: ラウンドUUID
            index_filter: all | nikkei225 | topix

        Returns:
            パフォーマンス統計
        """
        # 基本クエリ
        # prediction_hitはBoolean型なので、INTEGERにキャストしてからSUM
        from sqlalchemy import Integer, case

        stmt = (
            select(
                func.count(RoundResult.id).label("total_recommendations"),
                func.avg(RoundResult.predicted_return).label("avg_predicted_return"),
                func.avg(RoundResult.actual_return).label("avg_actual_return"),
                func.sum(
                    case((RoundResult.prediction_hit.is_(True), 1), else_=0)
                ).label("hit_count"),
            )
            .select_from(RoundResult)
            .where(RoundResult.round_id == round_uuid)
        )

        # 指数フィルター適用
        if index_filter != "all":
            stmt = stmt.join(
                StockMaster, RoundResult.stock_code == StockMaster.stock_code
            )
            if index_filter == "nikkei225":
                stmt = stmt.where(StockMaster.is_nikkei225.is_(True))
            elif index_filter == "topix":
                stmt = stmt.where(StockMaster.is_topix.is_(True))

        result = await self.session.execute(stmt)
        row = result.one()

        total = row.total_recommendations or 0
        hit_count = float(row.hit_count or 0)
        hit_rate = hit_count / total if total > 0 else 0.0

        return {
            "total_recommendations": total,
            "avg_predicted_return": float(row.avg_predicted_return or 0),
            "avg_actual_return": float(row.avg_actual_return or 0),
            "hit_rate": round(hit_rate, 4),
        }

    async def get_rounds_with_performance(
        self,
        round_type: str | None = None,
        index_filter: str = "all",
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict]:
        """ラウンド一覧をパフォーマンス統計付きで取得

        Args:
            round_type: BUY | SELL | None（全て）
            index_filter: all | nikkei225 | topix
            limit: 取得件数
            offset: オフセット

        Returns:
            ラウンド一覧（パフォーマンス統計付き）
        """
        # ラウンド一覧取得
        stmt = (
            select(Round)
            .where(Round.status == "CLOSED")
            .order_by(Round.start_date.desc())
            .limit(limit)
            .offset(offset)
        )

        if round_type:
            stmt = stmt.where(Round.round_type == round_type)

        result = await self.session.execute(stmt)
        rounds = list(result.scalars().all())

        # 各ラウンドのパフォーマンス統計を取得
        rounds_with_performance = []
        for round_obj in rounds:
            performance = await self.get_round_performance(
                round_obj.id, index_filter
            )
            rounds_with_performance.append(
                {"round": round_obj, "performance": performance}
            )

        return rounds_with_performance

    async def count_closed_rounds(self, round_type: str | None = None) -> int:
        """クローズ済みラウンド数をカウント"""
        stmt = select(func.count(Round.id)).where(Round.status == "CLOSED")
        if round_type:
            stmt = stmt.where(Round.round_type == round_type)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_overall_performance(
        self, round_type: str, index_filter: str = "all"
    ) -> dict:
        """全体のパフォーマンス統計を計算

        Args:
            round_type: BUY | SELL
            index_filter: all | nikkei225 | topix

        Returns:
            全体統計
        """
        # ラウンド一覧取得
        rounds_stmt = (
            select(Round.id)
            .where(Round.round_type == round_type, Round.status == "CLOSED")
        )
        rounds_result = await self.session.execute(rounds_stmt)
        round_uuids = [row[0] for row in rounds_result.all()]

        if not round_uuids:
            return {
                "total_rounds": 0,
                "avg_hit_rate": 0.0,
                "avg_predicted_return": 0.0,
                "avg_actual_return": 0.0,
                "total_profit_loss": 0.0,
            }

        # 基本統計クエリ
        from sqlalchemy import case

        stmt = (
            select(
                func.avg(RoundResult.predicted_return).label("avg_predicted"),
                func.avg(RoundResult.actual_return).label("avg_actual"),
                func.sum(RoundResult.profit_loss).label("total_profit_loss"),
                func.count(RoundResult.id).label("total_count"),
                func.sum(
                    case((RoundResult.prediction_hit.is_(True), 1), else_=0)
                ).label("hit_count"),
            )
            .select_from(RoundResult)
            .where(RoundResult.round_id.in_(round_uuids))
        )

        # 指数フィルター適用
        if index_filter != "all":
            stmt = stmt.join(
                StockMaster, RoundResult.stock_code == StockMaster.stock_code
            )
            if index_filter == "nikkei225":
                stmt = stmt.where(StockMaster.is_nikkei225.is_(True))
            elif index_filter == "topix":
                stmt = stmt.where(StockMaster.is_topix.is_(True))

        result = await self.session.execute(stmt)
        row = result.one()

        total_count = row.total_count or 0
        hit_count = float(row.hit_count or 0)
        avg_hit_rate = hit_count / total_count if total_count > 0 else 0.0

        return {
            "total_rounds": len(round_uuids),
            "avg_hit_rate": round(avg_hit_rate, 4),
            "avg_predicted_return": float(row.avg_predicted or 0),
            "avg_actual_return": float(row.avg_actual or 0),
            "total_profit_loss": float(row.total_profit_loss or 0),
        }
