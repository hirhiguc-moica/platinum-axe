"""ラウンド一覧取得UseCase"""

from dataclasses import dataclass

from app.domain.models import Round
from app.infrastructure.repositories.round_repository import RoundRepository


@dataclass
class GetRoundsInput:
    """入力パラメータ"""

    limit: int = 50
    offset: int = 0


@dataclass
class GetRoundsOutput:
    """出力データ"""

    rounds: list[Round]
    total: int


class GetRoundsUseCase:
    """ラウンド一覧取得UseCase"""

    def __init__(self, round_repository: RoundRepository):
        self.round_repository = round_repository

    async def execute(self, input_data: GetRoundsInput) -> GetRoundsOutput:
        """
        ラウンド一覧を取得

        Args:
            input_data: 入力パラメータ

        Returns:
            ラウンド一覧
        """
        # ラウンド一覧取得
        rounds = await self.round_repository.find_all(
            limit=input_data.limit, offset=input_data.offset
        )

        return GetRoundsOutput(rounds=rounds, total=len(rounds))
