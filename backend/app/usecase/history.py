"""ラウンド履歴関連ユースケース"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.round_repository import (
    RoundRecommendationRepository,
    RoundRepository,
)
from app.infrastructure.repositories.round_result_repository import (
    RoundResultRepository,
)


class GetLatestRoundResultsUseCase:
    """直近のラウンド結果取得ユースケース"""

    async def execute(
        self, session: AsyncSession, index_filter: str = "all"
    ) -> dict:
        """直近のBUY/SELLラウンド結果を取得

        Args:
            session: DBセッション
            index_filter: all | nikkei225 | topix

        Returns:
            直近のBUY/SELL結果
        """
        repo = RoundResultRepository(session)

        # 直近のクローズ済みラウンドを取得
        latest_rounds = await repo.get_latest_closed_rounds()

        buy_round = latest_rounds["buy"]
        sell_round = latest_rounds["sell"]

        result = {"buy_latest": None, "sell_latest": None}

        # BUYラウンドのパフォーマンス取得
        if buy_round:
            buy_performance = await repo.get_round_performance(
                buy_round.id, index_filter
            )
            result["buy_latest"] = {
                "round_id": buy_round.round_id,
                "start_date": buy_round.start_date.isoformat(),
                "end_date": buy_round.end_date.isoformat(),
                "avg_predicted_return": buy_performance["avg_predicted_return"],
                "avg_actual_return": buy_performance["avg_actual_return"],
                "hit_rate": buy_performance["hit_rate"],
                "total_recommendations": buy_performance["total_recommendations"],
            }

        # SELLラウンドのパフォーマンス取得
        if sell_round:
            sell_performance = await repo.get_round_performance(
                sell_round.id, index_filter
            )
            result["sell_latest"] = {
                "round_id": sell_round.round_id,
                "start_date": sell_round.start_date.isoformat(),
                "end_date": sell_round.end_date.isoformat(),
                "avg_predicted_return": sell_performance["avg_predicted_return"],
                "avg_actual_return": sell_performance["avg_actual_return"],
                "hit_rate": sell_performance["hit_rate"],
                "total_recommendations": sell_performance["total_recommendations"],
            }

        return result


class GetRoundHistoryUseCase:
    """ラウンド履歴取得ユースケース"""

    async def execute(
        self,
        session: AsyncSession,
        round_type: str | None = None,
        index_filter: str = "all",
        page: int = 1,
        limit: int = 10,
    ) -> dict:
        """ラウンド履歴を取得

        Args:
            session: DBセッション
            round_type: BUY | SELL | None
            index_filter: all | nikkei225 | topix
            page: ページ番号（1始まり）
            limit: 1ページあたりの件数

        Returns:
            ラウンド履歴とページネーション情報
        """
        repo = RoundResultRepository(session)

        # オフセット計算
        offset = (page - 1) * limit

        # ラウンド一覧取得
        rounds_data = await repo.get_rounds_with_performance(
            round_type=round_type,
            index_filter=index_filter,
            limit=limit,
            offset=offset,
        )

        # 総件数取得
        total = await repo.count_closed_rounds(round_type=round_type)
        total_pages = (total + limit - 1) // limit  # 切り上げ

        # レスポンス整形
        rounds = []
        for data in rounds_data:
            round_obj = data["round"]
            performance = data["performance"]
            rounds.append(
                {
                    "round_id": round_obj.round_id,
                    "round_type": round_obj.round_type,
                    "start_date": round_obj.start_date.isoformat(),
                    "end_date": round_obj.end_date.isoformat(),
                    "status": round_obj.status,
                    "performance": {
                        "total_recommendations": performance["total_recommendations"],
                        "avg_predicted_return": performance["avg_predicted_return"],
                        "avg_actual_return": performance["avg_actual_return"],
                        "hit_rate": performance["hit_rate"],
                    },
                }
            )

        return {
            "rounds": rounds,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
            },
        }


class GetOverallPerformanceUseCase:
    """全体パフォーマンス取得ユースケース"""

    async def execute(
        self, session: AsyncSession, index_filter: str = "all"
    ) -> dict:
        """全体パフォーマンス統計を取得

        Args:
            session: DBセッション
            index_filter: all | nikkei225 | topix

        Returns:
            BUY/SELLの全体統計
        """
        repo = RoundResultRepository(session)

        # BUY全体統計
        buy_performance = await repo.get_overall_performance("BUY", index_filter)

        # SELL全体統計
        sell_performance = await repo.get_overall_performance("SELL", index_filter)

        return {
            "buy_performance": buy_performance,
            "sell_performance": sell_performance,
        }


class GetRoundDetailWithResultsUseCase:
    """ラウンド詳細取得ユースケース（推奨銘柄 + 結果付き）"""

    async def execute(self, session: AsyncSession, round_id: str) -> dict | None:
        """ラウンド詳細を結果データ付きで取得

        Args:
            session: DBセッション
            round_id: ラウンドID（ビジネスキー、例: 2026-W29-BUY）

        Returns:
            ラウンド詳細 + 推奨銘柄 + 結果データ
            見つからない場合はNone
        """
        round_repo = RoundRepository(session)
        recommendation_repo = RoundRecommendationRepository(session)
        result_repo = RoundResultRepository(session)

        # ラウンド取得
        round_obj = await round_repo.find_by_id(round_id)
        if not round_obj:
            return None

        # 推奨銘柄取得
        recommendations = await recommendation_repo.find_by_round_uuid(round_obj.id)

        # 結果データ取得
        results = await result_repo.find_by_round_uuid(round_obj.id)
        results_dict = {r.stock_code: r for r in results}

        # 推奨銘柄と結果をマージ
        recommendations_with_results = []
        for rec in recommendations:
            result_data = results_dict.get(rec.stock_code)

            item = {
                "rank": rec.rank,
                "stock_code": rec.stock_code,
                "company_name": rec.stock.company_name if rec.stock else "",
                "sector_name": (
                    rec.stock.sector.sector_name
                    if rec.stock and rec.stock.sector
                    else ""
                ),
                "predicted_return": float(rec.predicted_return or 0),
                "confidence_score": float(rec.confidence_score or 0),
            }

            # 結果データがあれば追加
            if result_data:
                item.update(
                    {
                        "actual_return": float(result_data.actual_return or 0),
                        "prediction_error": float(result_data.prediction_error or 0),
                        "prediction_hit": result_data.prediction_hit,
                        "start_price": float(result_data.start_price or 0),
                        "end_price": float(result_data.end_price or 0),
                        "profit_loss": float(result_data.profit_loss or 0),
                    }
                )
            else:
                # 結果データがない場合（まだクローズしていないラウンド等）
                item.update(
                    {
                        "actual_return": None,
                        "prediction_error": None,
                        "prediction_hit": None,
                        "start_price": None,
                        "end_price": None,
                        "profit_loss": None,
                    }
                )

            recommendations_with_results.append(item)

        return {
            "round": {
                "round_id": round_obj.round_id,
                "round_type": round_obj.round_type,
                "start_date": round_obj.start_date.isoformat(),
                "end_date": round_obj.end_date.isoformat(),
                "status": round_obj.status,
            },
            "recommendations": recommendations_with_results,
        }
