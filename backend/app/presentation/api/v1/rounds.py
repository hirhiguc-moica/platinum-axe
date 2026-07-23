"""ラウンド関連API"""

from fastapi import APIRouter, Depends, HTTPException, Query

from app.infrastructure.repositories.round_repository import (
    RoundRecommendationRepository,
    RoundRepository,
)
from app.presentation.dependencies import (
    get_round_recommendation_repository,
    get_round_repository,
)
from app.presentation.schemas.round import (
    GetRoundRecommendationsResponse,
    GetRoundsResponse,
)
from app.usecase.rounds.get_round_recommendations import (
    GetRoundRecommendationsInput,
    GetRoundRecommendationsUseCase,
)
from app.usecase.rounds.get_rounds import GetRoundsInput, GetRoundsUseCase

router = APIRouter()


@router.get("/rounds", response_model=GetRoundsResponse)
async def get_rounds(
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    round_repository: RoundRepository = Depends(get_round_repository),
) -> GetRoundsResponse:
    """
    ラウンド一覧取得

    Args:
        limit: 取得件数（1〜100）
        offset: オフセット
        round_repository: RoundRepository

    Returns:
        ラウンド一覧
    """
    # UseCaseの実行
    usecase = GetRoundsUseCase(round_repository)
    input_data = GetRoundsInput(limit=limit, offset=offset)
    output = await usecase.execute(input_data)

    return GetRoundsResponse(rounds=output.rounds, total=output.total)


@router.get("/rounds/{round_id}/recommendations", response_model=GetRoundRecommendationsResponse)
async def get_round_recommendations(
    round_id: str,
    round_repository: RoundRepository = Depends(get_round_repository),
    recommendation_repository: RoundRecommendationRepository = Depends(
        get_round_recommendation_repository
    ),
) -> GetRoundRecommendationsResponse:
    """
    ラウンド推奨銘柄取得

    Args:
        round_id: ラウンドID（ビジネスキー、例: 2026-W30-BUY）
        round_repository: RoundRepository
        recommendation_repository: RoundRecommendationRepository

    Returns:
        ラウンド + 推奨銘柄リスト

    Raises:
        HTTPException: ラウンドが見つからない場合（404）
    """
    # UseCaseの実行
    usecase = GetRoundRecommendationsUseCase(round_repository, recommendation_repository)
    input_data = GetRoundRecommendationsInput(round_id=round_id)
    output = await usecase.execute(input_data)

    if output is None:
        raise HTTPException(status_code=404, detail=f"Round not found: {round_id}")

    return GetRoundRecommendationsResponse(
        round=output.round, recommendations=output.recommendations
    )
