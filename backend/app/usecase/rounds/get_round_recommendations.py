"""ラウンド推奨銘柄取得UseCase"""

from dataclasses import dataclass

from app.domain.models import Round, RoundRecommendation
from app.infrastructure.repositories.round_repository import (
    RoundRecommendationRepository,
    RoundRepository,
)


@dataclass
class GetRoundRecommendationsInput:
    """入力パラメータ"""

    round_id: str  # ビジネスキー（例: "2026-W30-BUY"）


@dataclass
class GetRoundRecommendationsOutput:
    """出力データ"""

    round: Round
    recommendations: list[RoundRecommendation]


class GetRoundRecommendationsUseCase:
    """ラウンド推奨銘柄取得UseCase"""

    def __init__(
        self,
        round_repository: RoundRepository,
        recommendation_repository: RoundRecommendationRepository,
    ):
        self.round_repository = round_repository
        self.recommendation_repository = recommendation_repository

    async def execute(
        self, input_data: GetRoundRecommendationsInput
    ) -> GetRoundRecommendationsOutput | None:
        """
        ラウンド推奨銘柄を取得

        Args:
            input_data: 入力パラメータ

        Returns:
            ラウンド + 推奨銘柄リスト（ラウンドが存在しない場合はNone）
        """
        # 1. ビジネスキーでRoundを検索
        round_entity = await self.round_repository.find_by_id(input_data.round_id)

        if round_entity is None:
            return None

        # 2. Round.id（UUID）でRoundRecommendationを検索
        recommendations = await self.recommendation_repository.find_by_round_uuid(round_entity.id)

        return GetRoundRecommendationsOutput(round=round_entity, recommendations=recommendations)
